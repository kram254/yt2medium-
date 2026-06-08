#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from content_library import save_post, get_post, init_db

TEMP_STORAGE_DIR = Path(__file__).parent / 'temp_posts'


def backfill_temp_to_library(dry_run=False, verbose=True):
    init_db()

    if not TEMP_STORAGE_DIR.exists():
        if verbose:
            print(f"No temp_posts directory found at {TEMP_STORAGE_DIR}")
        return {"processed": 0, "skipped": 0, "errors": 0, "total": 0}

    stats = {"processed": 0, "skipped": 0, "errors": 0, "total": 0}

    tenant_dirs = [d for d in TEMP_STORAGE_DIR.iterdir() if d.is_dir()]
    root_files = list(TEMP_STORAGE_DIR.glob('*.json'))

    all_files = []
    for tenant_dir in tenant_dirs:
        tenant_id = tenant_dir.name
        for f in tenant_dir.glob('*.json'):
            all_files.append((f, tenant_id))
    for f in root_files:
        all_files.append((f, 'legacy'))

    stats["total"] = len(all_files)

    if verbose:
        print(f"Found {len(all_files)} temp post files to process")
        print(f"  - {len(tenant_dirs)} tenant directories")
        print(f"  - {len(root_files)} root-level files (legacy)")

    for temp_file, tenant_id in all_files:
        post_id = temp_file.stem

        try:
            existing = get_post(post_id, tenant_id=tenant_id)
            if existing:
                if verbose:
                    print(f"  SKIP: {post_id} (tenant={tenant_id}) — already in library")
                stats["skipped"] += 1
                continue
        except Exception:
            pass

        try:
            with open(temp_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            if verbose:
                print(f"  ERROR: {post_id} — failed to read: {e}")
            stats["errors"] += 1
            continue

        markdown_content = data.get('blog_post_markdown', '') or data.get('markdown_content', '')
        html_content = data.get('blog_post_html', '') or data.get('html_content', '')

        if not markdown_content and not html_content:
            if verbose:
                print(f"  SKIP: {post_id} — no content")
            stats["skipped"] += 1
            continue

        post_data = {
            'id': post_id,
            'title': data.get('title', 'Untitled Post'),
            'markdown_content': markdown_content,
            'html_content': html_content,
            'source_url': data.get('source_url', ''),
            'source_type': data.get('source_type', data.get('input_type', 'topic')),
            'template': data.get('template', ''),
            'tone': data.get('tone', ''),
            'model': data.get('model', ''),
            'word_count': data.get('word_count', 0),
            'reading_time': data.get('reading_time', 0),
            'engagement_score': data.get('engagement_score', 0),
            'seo_score': data.get('seo_score', 0),
            'viral_potential': data.get('viral_potential', 0),
            'metadata': {
                'image_data': data.get('image_data'),
                'image_data_2': data.get('image_data_2'),
                'key_quotes': data.get('key_quotes', []),
                'readability_score': data.get('readability_score'),
                'seo_recommendations': data.get('seo_recommendations', []),
                'backfilled_at': datetime.now().isoformat(),
                'original_file': str(temp_file),
            }
        }

        if dry_run:
            if verbose:
                print(f"  DRY-RUN: {post_id} (tenant={tenant_id}) — would save")
            stats["processed"] += 1
            continue

        try:
            save_post(post_data, tenant_id=tenant_id)
            if verbose:
                print(f"  OK: {post_id} (tenant={tenant_id}) — saved to library")
            stats["processed"] += 1
        except Exception as e:
            if verbose:
                print(f"  ERROR: {post_id} — save failed: {e}")
            stats["errors"] += 1

    return stats


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Backfill temp_posts to content_library')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without saving')
    parser.add_argument('--quiet', action='store_true', help='Suppress verbose output')
    args = parser.parse_args()

    print("=" * 60)
    print("BACKFILL: temp_posts -> content_library")
    print("=" * 60)

    if args.dry_run:
        print("MODE: Dry run (no changes will be made)\n")
    else:
        print("MODE: Live (posts will be saved to SQLite)\n")

    stats = backfill_temp_to_library(dry_run=args.dry_run, verbose=not args.quiet)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Total files found:  {stats['total']}")
    print(f"  Successfully saved: {stats['processed']}")
    print(f"  Skipped (existing): {stats['skipped']}")
    print(f"  Errors:             {stats['errors']}")

    if not args.dry_run and stats['processed'] > 0:
        print(f"\n{stats['processed']} posts now available in content_library.db")
        print("Access via /api/library endpoint")


if __name__ == '__main__':
    main()
