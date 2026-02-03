"""Command-line interface for SampleSheriff.

This module provides the main CLI using Typer, with commands for validating
sample sheets, managing schemas, and generating templates.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from samplesheriff import __version__
from samplesheriff.io import read_sample_sheet
from samplesheriff.reporting import (
    ProgressReporter,
    Reporter,
    ReportFormat,
    create_report_from_issues,
)
from samplesheriff.rules import DomainRule, FileRule, RuleEngine, SchemaRule, ValidationContext
from samplesheriff.schema import (
    ColumnSchema,
    ColumnType,
    Constraint,
    ConstraintType,
    FileCheckMode,
    Schema,
    list_builtin_schemas,
    load_builtin_schema,
)

app = typer.Typer(
    name="samplesheriff",
    help="A fast, strict, nf-core-style sample sheet validator for bioinformatics pipelines",
    no_args_is_help=True,
)
console = Console()

# Subcommands
schema_app = typer.Typer(help="Schema management commands")
app.add_typer(schema_app, name="schema")


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"SampleSheriff {__version__}")
        raise typer.Exit()


@app.callback()
def cli_main(
    version: Annotated[
        bool,
        typer.Option("--version", "-v", callback=version_callback, is_eager=True),
    ] = False,
) -> None:
    """SampleSheriff: Validate bioinformatics sample sheets."""
    pass


@app.command()
def validate(
    input: Annotated[
        Path,
        typer.Option(
            "--input",
            "-i",
            help="Path to the sample sheet to validate",
            exists=True,
            readable=True,
            dir_okay=False,
        ),
    ],
    schema: Annotated[
        str,
        typer.Option(
            "--schema",
            "-s",
            help="Schema to use (builtin:name or path to schema file)",
        ),
    ] = "builtin:nfcore_like",
    base_dir: Annotated[
        Path | None,
        typer.Option(
            "--base-dir",
            "-b",
            help="Base directory for relative file paths",
            exists=True,
            file_okay=False,
            dir_okay=True,
        ),
    ] = None,
    strict: Annotated[
        bool,
        typer.Option(
            "--strict",
            help="Treat warnings as errors and fail on extra columns",
        ),
    ] = False,
    report: Annotated[
        Path | None,
        typer.Option(
            "--report",
            "-r",
            help="Path to write JSON report",
            dir_okay=False,
        ),
    ] = None,
    format: Annotated[
        ReportFormat,
        typer.Option(
            "--format",
            "-f",
            help="Output format",
            case_sensitive=False,
        ),
    ] = ReportFormat.TEXT,
    fail_on: Annotated[
        str,
        typer.Option(
            "--fail-on",
            help="Fail on 'errors' or 'warnings'",
        ),
    ] = "errors",
    require_index: Annotated[
        bool,
        typer.Option(
            "--require-index",
            help="Require index files for BAM/CRAM/VCF",
        ),
    ] = False,
    peek: Annotated[
        int,
        typer.Option(
            "--peek",
            "-p",
            help="Number of FASTQ reads to peek at for pairing validation (0 to disable)",
            min=0,
        ),
    ] = 0,
    quiet: Annotated[
        bool,
        typer.Option(
            "--quiet",
            "-q",
            help="Suppress progress output",
        ),
    ] = False,
) -> None:
    """Validate a sample sheet against a schema."""
    progress = ProgressReporter(console, quiet)
    reporter = Reporter(console)

    try:
        # Load schema
        progress.info(f"Loading schema: {schema}")
        if schema.startswith("builtin:"):
            schema_obj = load_builtin_schema(schema)
        else:
            schema_path = Path(schema)
            if not schema_path.exists():
                console.print(f"[red]Schema file not found: {schema}[/red]")
                sys.exit(2)
            schema_obj = Schema.from_file(schema_path)
        progress.success(f"Loaded schema: {schema_obj.name}")

        # Create reader
        reader = read_sample_sheet(input, schema_obj)
        progress.info(f"Detected delimiter: {repr(reader.delimiter)}")

        # Set up validation context
        context = ValidationContext(
            input_path=input,
            schema=schema_obj,
            base_dir=base_dir,
            strict=strict,
            require_index=require_index,
            peek_fastq=peek,
            headers=reader.read_headers(),
        )

        # Initialize rule engine
        engine = RuleEngine()
        engine.initialize(context)

        # Add rules
        engine.add_rule(SchemaRule(schema_obj))
        engine.add_rule(FileRule())
        engine.add_rule(
            DomainRule(
                require_index=require_index,
                peek_fastq=peek,
            )
        )

        # Validate
        progress.info("Starting validation...")
        all_issues = []
        row_count = 0

        for row_number, row in enumerate(reader.iter_rows(), start=1):
            row_count += 1
            issues = engine.validate_row(row, row_number)
            all_issues.extend(issues)

            if row_number % 1000 == 0 and not quiet:
                progress.progress(row_number, reader.count_rows(), f"Validated {row_number} rows")

        # Finalize
        final_issues = engine.finalize()
        all_issues.extend(final_issues)

        # Create report
        report_obj = create_report_from_issues(
            input_file=str(input),
            schema_name=schema_obj.name,
            issues=all_issues,
            total_rows=row_count,
            metadata={
                "delimiter": reader.delimiter,
                "schema_version": schema_obj.version,
            },
        )

        # Save JSON report if requested
        if report:
            reporter.save_report(report_obj, report)
            progress.success(f"Report saved to: {report}")

        # Print report
        fail_on_warnings = fail_on == "warnings"
        exit_code = reporter.print_report(report_obj, format, fail_on_warnings)

        sys.exit(exit_code)

    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(2)
    except PermissionError as e:
        console.print(f"[red]Permission denied: {e}[/red]")
        sys.exit(2)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        if not quiet:
            import traceback

            console.print(traceback.format_exc())
        sys.exit(2)


@schema_app.command("list")
def schema_list(
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Show detailed information"),
    ] = False,
) -> None:
    """List available built-in schemas."""
    schemas = list_builtin_schemas()

    if not schemas:
        console.print("[yellow]No built-in schemas found.[/yellow]")
        return

    if verbose:
        table = Table(title="Available Schemas")
        table.add_column("Name", style="cyan")
        table.add_column("Description", style="white")

        for name, description in sorted(schemas.items()):
            table.add_row(name, description)

        console.print(table)
    else:
        console.print("[bold]Available schemas:[/bold]")
        for name in sorted(schemas.keys()):
            console.print(f"  • {name}")
        console.print("\nUse 'samplesheriff schema show <name>' for details")


@schema_app.command("show")
def schema_show(
    name: Annotated[
        str,
        typer.Argument(help="Schema name (with or without 'builtin:' prefix)"),
    ],
) -> None:
    """Show details of a built-in schema."""
    try:
        schema_obj = load_builtin_schema(name)

        console.print(
            Panel.fit(
                f"[bold]{schema_obj.name}[/bold]\n"
                f"Version: {schema_obj.version}\n"
                f"{schema_obj.description}"
            )
        )

        # Columns table
        table = Table(title="Columns")
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Required", style="yellow")
        table.add_column("Description", style="white")

        for col in schema_obj.columns:
            table.add_row(
                col.name,
                col.type.name.lower(),
                "✓" if col.required else "",
                col.description,
            )

        console.print(table)

        # Constraints
        if schema_obj.constraints:
            console.print("\n[bold]Constraints:[/bold]")
            for constraint in schema_obj.constraints:
                console.print(f"  • {constraint.type.value}: {', '.join(constraint.columns)}")

    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@app.command()
def init(
    output_dir: Annotated[
        Path,
        typer.Argument(help="Directory to create template files"),
    ] = Path("."),
    name: Annotated[
        str,
        typer.Option("--name", "-n", help="Base name for template files"),
    ] = "samplesheet",
    type: Annotated[
        str,
        typer.Option("--type", "-t", help="Template type: fastq, bam, vcf, or minimal"),
    ] = "fastq",
) -> None:
    """Generate a template sample sheet and schema."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create sample sheet based on type
    sheet_path = output_dir / f"{name}.tsv"
    schema_path = output_dir / f"{name}_schema.yaml"

    templates = {
        "fastq": _create_fastq_template(),
        "bam": _create_bam_template(),
        "vcf": _create_vcf_template(),
        "minimal": _create_minimal_template(),
    }

    if type not in templates:
        console.print(f"[red]Unknown template type: {type}[/red]")
        console.print(f"Available types: {', '.join(templates.keys())}")
        sys.exit(1)

    sheet_content, schema_obj = templates[type]

    # Write files
    with open(sheet_path, "w") as f:
        f.write(sheet_content)
    console.print(f"[green]✓[/green] Created sample sheet: {sheet_path}")

    schema_obj.save(schema_path)
    console.print(f"[green]✓[/green] Created schema: {schema_path}")

    console.print("\n[bold]Next steps:[/bold]")
    console.print(f"  1. Edit {sheet_path} with your sample information")
    console.print(f"  2. Validate with: samplesheriff validate -i {sheet_path} -s {schema_path}")


def _create_fastq_template() -> tuple[str, Schema]:
    """Create FASTQ template."""
    sheet = """sample\tfastq_1\tfastq_2\tstrandedness
sample1\tpath/to/sample1_R1.fastq.gz\tpath/to/sample1_R2.fastq.gz\tauto
sample2\tpath/to/sample2_R1.fastq.gz\tpath/to/sample2_R2.fastq.gz\tauto
"""

    schema = Schema(
        name="fastq_template",
        description="Template schema for paired-end FASTQ samples",
        delimiter="\t",
        columns=[
            ColumnSchema(
                name="sample",
                type=ColumnType.STRING,
                required=True,
                description="Sample identifier",
            ),
            ColumnSchema(
                name="fastq_1",
                type=ColumnType.PATH,
                required=True,
                file_check=FileCheckMode.REQUIRED,
                description="Path to R1 FASTQ file",
            ),
            ColumnSchema(
                name="fastq_2",
                type=ColumnType.PATH,
                required=True,
                file_check=FileCheckMode.REQUIRED,
                description="Path to R2 FASTQ file",
            ),
            ColumnSchema(
                name="strandedness",
                type=ColumnType.STRING,
                required=False,
                allowed_values=["auto", "forward", "reverse", "unstranded"],
                description="Library strandedness",
            ),
        ],
        constraints=[
            Constraint(
                type=ConstraintType.UNIQUE,
                columns=["sample"],
            ),
        ],
    )

    return sheet, schema


def _create_bam_template() -> tuple[str, Schema]:
    """Create BAM template."""
    sheet = """sample\tbam\tsample_type
sample1\tpath/to/sample1.bam\ttumor
sample2\tpath/to/sample2.bam\tnormal
"""

    schema = Schema(
        name="bam_template",
        description="Template schema for BAM samples",
        delimiter="\t",
        columns=[
            ColumnSchema(
                name="sample",
                type=ColumnType.STRING,
                required=True,
                description="Sample identifier",
            ),
            ColumnSchema(
                name="bam",
                type=ColumnType.PATH,
                required=True,
                file_check=FileCheckMode.REQUIRED,
                description="Path to BAM file",
            ),
            ColumnSchema(
                name="sample_type",
                type=ColumnType.STRING,
                required=False,
                allowed_values=["tumor", "normal", "control"],
                description="Sample type classification",
            ),
        ],
        constraints=[
            Constraint(
                type=ConstraintType.UNIQUE,
                columns=["sample"],
            ),
        ],
    )

    return sheet, schema


def _create_vcf_template() -> tuple[str, Schema]:
    """Create VCF template."""
    sheet = """sample\tvcf\tcaller
sample1\tpath/to/sample1.vcf.gz\thaplotypecaller
sample2\tpath/to/sample2.vcf.gz\tdeepvariant
"""

    schema = Schema(
        name="vcf_template",
        description="Template schema for VCF samples",
        delimiter="\t",
        columns=[
            ColumnSchema(
                name="sample",
                type=ColumnType.STRING,
                required=True,
                description="Sample identifier",
            ),
            ColumnSchema(
                name="vcf",
                type=ColumnType.PATH,
                required=True,
                file_check=FileCheckMode.REQUIRED,
                description="Path to VCF file",
            ),
            ColumnSchema(
                name="caller",
                type=ColumnType.STRING,
                required=False,
                description="Variant caller used",
            ),
        ],
        constraints=[
            Constraint(
                type=ConstraintType.UNIQUE,
                columns=["sample"],
            ),
        ],
    )

    return sheet, schema


def _create_minimal_template() -> tuple[str, Schema]:
    """Create minimal template."""
    sheet = """sample\tfile_path
sample1\tpath/to/file1
sample2\tpath/to/file2
"""

    schema = Schema(
        name="minimal_template",
        description="Minimal template with just sample and file",
        delimiter="\t",
        columns=[
            ColumnSchema(
                name="sample",
                type=ColumnType.STRING,
                required=True,
                description="Sample identifier",
            ),
            ColumnSchema(
                name="file_path",
                type=ColumnType.PATH,
                required=True,
                file_check=FileCheckMode.REQUIRED,
                description="Path to data file",
            ),
        ],
        constraints=[
            Constraint(
                type=ConstraintType.UNIQUE,
                columns=["sample"],
            ),
        ],
    )

    return sheet, schema


def main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
