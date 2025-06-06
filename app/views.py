import time

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .forms import StatsFilterForm
from django.db import connection

def raw_query(sql, params=None):
    with connection.cursor() as cursor:
        cursor.execute(sql, params or [])
        columns = [col[0] for col in cursor.description]
        return [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

@login_required
def stats_view(request):
    start_time = time.time()
    results = []
    stats = None
    elapsed = None

    if request.method == "POST":
        form = StatsFilterForm(request.POST)
        if form.is_valid():
            pf, pt = form.cleaned_data['publication_from'], form.cleaned_data['publication_to']
            of, ot = form.cleaned_data['operation_from'], form.cleaned_data['operation_to']
            keyword = form.cleaned_data['keyword']

            sql = """
                WITH filtered_ops AS (
                    SELECT * FROM business_agreement_operations
                    WHERE created_at BETWEEN %s AND %s
                ),
                filtered_videos AS (
                    SELECT id, published_at, limit_type
                    FROM content_vod_video_projects
                    WHERE published_at BETWEEN %s AND %s
                      AND id IN (SELECT video_project_id FROM filtered_ops)
                ),
                filtered_titles AS (
                    SELECT content_vod_video_project_id, title
                    FROM content_vod_video_project_translations
                    WHERE content_vod_video_project_id IN (SELECT id FROM filtered_videos)
                      AND title ILIKE %s
                ),
                main_data AS (
                    SELECT
                        o.id as op_id,
                        o.agreement_id,
                        v.id as video_id,
                        v.limit_type,
                        t.title
                    FROM filtered_ops o
                    JOIN filtered_videos v ON o.video_project_id = v.id
                    JOIN filtered_titles t ON v.id = t.content_vod_video_project_id
                )
                SELECT
                    d.video_id,
                    d.title,
                    d.limit_type,
                    COUNT(d.op_id) as download_count,
                    ARRAY_AGG(DISTINCT d.agreement_id) as agreement_ids
                FROM main_data d
                GROUP BY d.video_id, d.title, d.limit_type
            """

            main_rows = raw_query(sql, [of, ot, pf, pt, f"%{keyword}%"])

            if not main_rows:
                return render(request, 'app/stats.html', {
                    "form": form, "stats": None, "results": [], "elapsed": None,
                })

            all_agreement_ids = set()
            for row in main_rows:
                all_agreement_ids.update(row["agreement_ids"] or [])

            if all_agreement_ids:
                agr_rows = raw_query(
                    "SELECT id, company_id FROM business_agreements WHERE id = ANY(%s)",
                    [list(all_agreement_ids)]
                )
                agr_map = {row["id"]: row["company_id"] for row in agr_rows}

                all_company_ids = set(row["company_id"] for row in agr_rows if row["company_id"])
                comp_rows = raw_query(
                    "SELECT id, name FROM business_companies WHERE id = ANY(%s)",
                    [list(all_company_ids)]
                )
                comp_map = {row["id"]: row["name"] for row in comp_rows}
            else:
                agr_map = {}
                comp_map = {}

            all_video_ids = [row["video_id"] for row in main_rows]
            tag_conn_rows = raw_query(
                "SELECT connectable_id, tag_id FROM content_tag_connections WHERE connectable_id = ANY(%s)",
                [all_video_ids]
            )
            tags_by_video = {}
            for row in tag_conn_rows:
                tags_by_video.setdefault(row["connectable_id"], set()).add(row["tag_id"])

            all_tag_ids = set(row["tag_id"] for row in tag_conn_rows)
            tag_trans_rows = raw_query(
                "SELECT content_tag_id, name FROM content_tag_translations WHERE content_tag_id = ANY(%s)",
                [list(all_tag_ids)]
            )
            tag_map = {row["content_tag_id"]: row["name"] for row in tag_trans_rows}

            results = []
            all_clients_set = set()
            for row in main_rows:
                agreement_ids = [aid for aid in (row["agreement_ids"] or []) if aid]
                client_ids = [agr_map.get(aid) for aid in agreement_ids if agr_map.get(aid)]
                client_names = [comp_map.get(cid) for cid in client_ids if comp_map.get(cid)]
                all_clients_set.update(client_names)

                video_tags = [tag_map.get(tag_id) for tag_id in tags_by_video.get(row["video_id"], []) if tag_map.get(tag_id)]

                results.append({
                    "download_count": row["download_count"],
                    "title": row["title"] or "",
                    "tags": ", ".join(video_tags) if video_tags else "—",
                    "rights_type": row["limit_type"] or "",
                    "clients": ", ".join(client_names) if client_names else "—"
                })

            stats = {
                "keyword": keyword,
                "videos": len(results),
                "downloads": sum(row["download_count"] for row in main_rows),
                "clients": len([c for c in all_clients_set if c])
            }

            elapsed = time.time() - start_time
    else:
        form = StatsFilterForm()

    return render(request, 'app/stats.html', {
        "form": form,
        "stats": stats,
        "results": results,
        "elapsed": elapsed,
    })




