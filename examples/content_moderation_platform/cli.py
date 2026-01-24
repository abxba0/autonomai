#!/usr/bin/env python3
"""
Command-Line Interface for Content Moderation Platform

Usage:
    python cli.py moderate --text "Content to moderate" --tenant gaming_community
    python cli.py batch --file contents.json --tenant social_platform
    python cli.py stats --tenant gaming_community
"""

import click
import json
from pathlib import Path
from engine import ModerationEngine
from dotenv import load_dotenv
import os


@click.group()
def cli():
    """Content Moderation Platform CLI"""
    load_dotenv()


@cli.command()
@click.option('--text', required=True, help='Content text to moderate')
@click.option('--tenant', default='default', help='Tenant ID')
@click.option('--type', default='comment', help='Content type')
@click.option('--author', default='cli_user', help='Author ID')
def moderate(text, tenant, type, author):
    """Moderate a single piece of content"""

    click.echo(f"\n🔍 Moderating content for tenant '{tenant}'...\n")

    engine = ModerationEngine(tenant_id=tenant)
    result = engine.moderate_content(
        content=text,
        content_type=type,
        author_id=author
    )

    # Display result
    status_color = {
        'approved': 'green',
        'rejected': 'red',
        'flagged': 'yellow'
    }.get(result['decision'], 'white')

    click.echo(f"Content: \"{text}\"")
    click.echo(f"Decision: ", nl=False)
    click.secho(result['decision'].upper(), fg=status_color, bold=True)
    click.echo(f"Action: {result['action']}")
    click.echo(f"Confidence: {result['confidence']:.2f}")

    if result['violations']:
        click.echo(f"\nViolations Found:")
        for v in result['violations']:
            click.echo(f"  - {v['type']}: severity {v['severity']:.2f}")

    click.echo(f"\nProcessing Time: {result['processing_time_ms']:.1f}ms")
    click.echo(f"From Cache: {result['from_cache']}")


@cli.command()
@click.option('--file', required=True, type=click.Path(exists=True), help='JSON file with content array')
@click.option('--tenant', default='default', help='Tenant ID')
def batch(file, tenant):
    """Moderate a batch of content from JSON file"""

    with open(file, 'r') as f:
        contents = json.load(f)

    click.echo(f"\n📦 Processing {len(contents)} items for tenant '{tenant}'...\n")

    engine = ModerationEngine(tenant_id=tenant)
    results = engine.moderate_batch(contents)

    # Summary
    approved = sum(1 for r in results if r['decision'] == 'approved')
    rejected = sum(1 for r in results if r['decision'] == 'rejected')
    flagged = sum(1 for r in results if r['decision'] == 'flagged')

    click.echo("Results:")
    click.secho(f"  ✅ Approved: {approved}", fg='green')
    click.secho(f"  ❌ Rejected: {rejected}", fg='red')
    click.secho(f"  ⚠️  Flagged: {flagged}", fg='yellow')

    # Save results
    output_file = Path(file).stem + '_results.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    click.echo(f"\n💾 Results saved to {output_file}")


@cli.command()
@click.option('--tenant', required=True, help='Tenant ID')
@click.option('--period', default='last_7_days', help='Time period')
def stats(tenant, period):
    """Show moderation statistics"""

    engine = ModerationEngine(tenant_id=tenant)
    stats = engine.get_moderation_stats(date_range=period)

    click.echo(f"\n📊 Statistics for '{stats['tenant_name']}' ({period})\n")
    click.echo(f"Total Moderated: {stats['total']:,}")
    click.secho(f"  Approved: {stats['approved']:,} ({stats['approval_rate']:.1%})", fg='green')
    click.secho(f"  Rejected: {stats['rejected']:,} ({stats['rejection_rate']:.1%})", fg='red')
    click.secho(f"  Flagged: {stats['flagged']:,} ({stats['flagged_rate']:.1%})", fg='yellow')
    click.echo(f"\nQuality:")
    click.echo(f"  Override Rate: {stats['override_rate']:.1%}")
    click.echo(f"  Avg Processing Time: {stats['avg_processing_time_ms']:.0f}ms")
    click.echo(f"  Cache Hit Rate: {stats['cache_hit_rate']:.1%}")


if __name__ == '__main__':
    cli()
