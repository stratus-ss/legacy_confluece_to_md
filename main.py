#!/usr/bin/env python3
"""
Unified entry point for Confluence downloading and PDF-to-Markdown conversion.
Supports independent operations and chained workflows.
"""

import os
import sys
from pathlib import Path
from typing import Optional

import click
from dotenv import load_dotenv

from modules.downloader import ConfluenceDownloader
from modules.pdf_converter.converter import PDFToMarkdownConverter, PDFConversionError
from modules.pdf_converter.config import load_config, setup_logging


def load_confluence_config() -> dict:
    """Load Confluence configuration from environment variables"""
    load_dotenv()
    
    return {
        'url': os.getenv('CONFLUENCE_URL', 'https://confluence.example.com'),
        'username': os.getenv('CONFLUENCE_USERNAME', 'admin'),
        'password': os.getenv('CONFLUENCE_PASSWORD', 'password'),
        'space_key': os.getenv('CONFLUENCE_SPACE_KEY', 'TEST'),
        'parent_page_title': os.getenv('CONFLUENCE_PARENT_PAGE_TITLE', 'Root Page'),
        'output_dir': os.getenv('CONFLUENCE_OUTPUT_DIR', './output/pdfs'),
        'attachments_dir': os.getenv('CONFLUENCE_ATTACHMENTS_DIR', './output/attachments'),
        'verify_ssl': os.getenv('CONFLUENCE_VERIFY_SSL', 'true').lower() == 'true'
    }


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option("--cpu-only", is_flag=True, help="Force CPU-only processing for PDF conversion")
@click.pass_context
def cli(ctx, verbose, cpu_only):
    """Confluence to Markdown Converter
    
    Download PDFs from Confluence and/or convert them to clean Markdown.
    Can run operations independently or chain them together.
    """
    ctx.ensure_object(dict)
    
    # Load configurations
    ctx.obj['confluence_config'] = load_confluence_config()
    ctx.obj['pdf_config'] = load_config()
    ctx.obj['verbose'] = verbose
    ctx.obj['cpu_only'] = cpu_only
    
    # Setup logging
    log_level = "DEBUG" if verbose else ctx.obj['pdf_config'].get("converter", {}).get("log_level", "INFO")
    setup_logging(log_level)


@cli.command()
@click.option("--parent-page", "-p", help="Override parent page title from .env")
@click.option("--space", "-s", help="Override space key from .env")
@click.option("--output-dir", "-o", help="Override output directory from .env")
@click.option("--attachments-dir", "-a", help="Override attachments directory from .env")
@click.pass_context
def download(ctx, parent_page, space, output_dir, attachments_dir):
    """Download PDFs from Confluence pages recursively"""
    
    config = ctx.obj['confluence_config'].copy()
    
    # Override with command line options if provided
    if parent_page:
        config['parent_page_title'] = parent_page
    if space:
        config['space_key'] = space  
    if output_dir:
        config['output_dir'] = output_dir
    if attachments_dir:
        config['attachments_dir'] = attachments_dir
        
    click.echo("🚀 Starting Confluence PDF download...")
    click.echo(f"📍 URL: {config['url']}")
    click.echo(f"📂 Space: {config['space_key']}")
    click.echo(f"📄 Parent Page: {config['parent_page_title']}")
    click.echo(f"💾 PDF Directory: {config['output_dir']}")
    click.echo(f"📎 Attachments Directory: {config['attachments_dir']}")
    
    try:
        # Create downloader
        downloader = ConfluenceDownloader(
            confluence_url=config['url'],
            username=config['username'],
            password=config['password'],
            space_key=config['space_key'],
            output_dir=config['output_dir'],
            attachments_dir=config['attachments_dir'],
            verify_ssl=config['verify_ssl']
        )
        
        # Download PDFs
        success = downloader.run(config['parent_page_title'])
        
        if success:
            click.echo("✅ Confluence download completed successfully!")
            click.echo(f"📁 PDFs saved to: {config['output_dir']}")
        else:
            click.echo("❌ Confluence download failed!", err=True)
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ Download error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("pdf_source", required=False)
@click.option("--output-dir", "-o", help="Override output directory from .env")
@click.option("--pattern", "-p", default="*.pdf", help="PDF file pattern for directory conversion")
@click.pass_context
def convert(ctx, pdf_source, output_dir, pattern):
    """Convert PDFs to Markdown
    
    PDF_SOURCE can be:
    - A single PDF file path
    - A directory containing PDFs
    - Omitted to use Confluence output directory
    """
    
    pdf_config = ctx.obj['pdf_config']
    confluence_config = ctx.obj['confluence_config']
    
    # Determine PDF source
    if pdf_source:
        pdf_source_path = Path(pdf_source)
    else:
        # Use Confluence output directory by default
        pdf_source_path = Path(confluence_config['output_dir'])
        click.echo(f"📂 Using Confluence output directory: {pdf_source_path}")
    
    if not pdf_source_path.exists():
        click.echo(f"❌ PDF source not found: {pdf_source_path}", err=True)
        sys.exit(1)
    
    # Determine output directory
    if output_dir:
        output_dir_path = Path(output_dir)
    else:
        output_dir_path = Path(pdf_config.get("output", {}).get("output_dir", "output/markdown"))
    
    output_dir_path.mkdir(parents=True, exist_ok=True)
    
    # Setup converter
    config_prefer_gpu = pdf_config.get("converter", {}).get("prefer_gpu", True)
    prefer_gpu = config_prefer_gpu and not ctx.obj['cpu_only']
    converter = PDFToMarkdownConverter(prefer_gpu=prefer_gpu)
    
    click.echo("🔄 Starting PDF to Markdown conversion...")
    click.echo(f"📁 Source: {pdf_source_path}")
    click.echo(f"💾 Output: {output_dir_path}")
    
    try:
        if pdf_source_path.is_file():
            # Single file conversion
            output_file = output_dir_path / f"{pdf_source_path.stem}.md"
            converter.convert_pdf(pdf_source_path, output_file)
            click.echo("✅ Conversion completed successfully!")
            click.echo(f"📄 Output saved to: {output_file}")
            
        elif pdf_source_path.is_dir():
            # Batch conversion
            pdf_files = list(pdf_source_path.glob(pattern))
            
            if not pdf_files:
                click.echo(f"❌ No PDF files found matching pattern '{pattern}' in {pdf_source_path}", err=True)
                sys.exit(1)
            
            click.echo(f"📊 Found {len(pdf_files)} PDF files to convert")
            
            results = converter.batch_convert(pdf_files, output_dir_path)
            
            click.echo("✅ Batch conversion completed!")
            click.echo(f"📈 Success: {len(results['success'])} files")
            if results["failed"]:
                click.echo(f"❌ Failed: {len(results['failed'])} files")
                for failed_file in results["failed"]:
                    click.echo(f"   - {failed_file}")
        else:
            click.echo(f"❌ Invalid PDF source: {pdf_source_path}", err=True)
            sys.exit(1)
            
    except PDFConversionError as e:
        click.echo(f"❌ Conversion failed: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--parent-page", "-p", help="Override parent page title from .env")
@click.option("--space", "-s", help="Override space key from .env") 
@click.option("--confluence-output", help="Override Confluence output directory from .env")
@click.option("--attachments-dir", help="Override attachments directory from .env")
@click.option("--markdown-output", help="Override Markdown output directory from .env")
@click.option("--pattern", default="*.pdf", help="PDF file pattern for conversion")
@click.pass_context
def workflow(ctx, parent_page, space, confluence_output, attachments_dir, markdown_output, pattern):
    """Complete workflow: Download from Confluence then convert to Markdown
    
    This chains the download and convert operations together.
    """
    
    confluence_config = ctx.obj['confluence_config'].copy()
    pdf_config = ctx.obj['pdf_config']
    
    # Override configurations
    if parent_page:
        confluence_config['parent_page_title'] = parent_page
    if space:
        confluence_config['space_key'] = space
    if confluence_output:
        confluence_config['output_dir'] = confluence_output
    if attachments_dir:
        confluence_config['attachments_dir'] = attachments_dir
    
    markdown_output_dir = markdown_output or pdf_config.get("output", {}).get("output_dir", "output/markdown")
    
    click.echo("🚀 Starting complete Confluence → Markdown workflow...")
    click.echo("=" * 50)
    
    # Step 1: Download from Confluence
    click.echo("📥 STEP 1: Downloading PDFs from Confluence")
    click.echo(f"📍 URL: {confluence_config['url']}")
    click.echo(f"📂 Space: {confluence_config['space_key']}")  
    click.echo(f"📄 Parent Page: {confluence_config['parent_page_title']}")
    click.echo(f"💾 PDF Output: {confluence_config['output_dir']}")
    click.echo(f"📎 Attachments Output: {confluence_config['attachments_dir']}")
    
    try:
        downloader = ConfluenceDownloader(
            confluence_url=confluence_config['url'],
            username=confluence_config['username'],
            password=confluence_config['password'],
            space_key=confluence_config['space_key'],
            output_dir=confluence_config['output_dir'],
            attachments_dir=confluence_config['attachments_dir'],
            verify_ssl=confluence_config['verify_ssl']
        )
        
        success = downloader.run(confluence_config['parent_page_title'])
        
        if not success:
            click.echo("❌ Confluence download failed - aborting workflow", err=True)
            sys.exit(1)
            
        click.echo("✅ Confluence download completed!")
        
    except Exception as e:
        click.echo(f"❌ Download error: {e}", err=True)
        sys.exit(1)
    
    # Step 2: Convert PDFs to Markdown
    click.echo("\n🔄 STEP 2: Converting PDFs to Markdown")
    pdf_source_dir = Path(confluence_config['output_dir'])
    markdown_output_path = Path(markdown_output_dir)
    markdown_output_path.mkdir(parents=True, exist_ok=True)
    
    click.echo(f"📁 PDF Source: {pdf_source_dir}")
    click.echo(f"💾 Markdown Output: {markdown_output_path}")
    
    try:
        pdf_files = list(pdf_source_dir.glob(pattern))
        
        if not pdf_files:
            click.echo(f"⚠️  No PDF files found matching pattern '{pattern}' in {pdf_source_dir}")
            click.echo("Confluence download completed but no PDFs to convert.")
            return
        
        click.echo(f"📊 Found {len(pdf_files)} PDF files to convert")
        
        # Setup converter
        config_prefer_gpu = pdf_config.get("converter", {}).get("prefer_gpu", True)
        prefer_gpu = config_prefer_gpu and not ctx.obj['cpu_only']
        converter = PDFToMarkdownConverter(prefer_gpu=prefer_gpu)
        
        results = converter.batch_convert(pdf_files, markdown_output_path)
        
        click.echo("✅ PDF conversion completed!")
        click.echo(f"📈 Success: {len(results['success'])} files")
        if results["failed"]:
            click.echo(f"❌ Failed: {len(results['failed'])} files")
            for failed_file in results["failed"]:
                click.echo(f"   - {failed_file}")
        
        click.echo("\n🎉 WORKFLOW COMPLETE!")
        click.echo(f"📁 PDFs: {pdf_source_dir}")
        click.echo(f"📝 Markdown: {markdown_output_path}")
        
    except Exception as e:
        click.echo(f"❌ Conversion error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context  
def info(ctx):
    """Show current configuration and system information"""
    
    confluence_config = ctx.obj['confluence_config']
    pdf_config = ctx.obj['pdf_config']
    
    click.echo("📋 Confluence to Markdown Converter - Configuration")
    click.echo("=" * 60)
    
    click.echo("\n🔗 CONFLUENCE SETTINGS:")
    click.echo(f"URL: {confluence_config['url']}")
    click.echo(f"Username: {confluence_config['username']}")
    click.echo(f"Space Key: {confluence_config['space_key']}")
    click.echo(f"Parent Page: {confluence_config['parent_page_title']}")
    click.echo(f"PDF Output: {confluence_config['output_dir']}")
    click.echo(f"Attachments Output: {confluence_config['attachments_dir']}")
    click.echo(f"SSL Verification: {'✅ Enabled' if confluence_config['verify_ssl'] else '❌ Disabled'}")
    
    click.echo("\n📄 PDF CONVERTER SETTINGS:")
    converter_config = pdf_config.get("converter", {})
    output_config = pdf_config.get("output", {})
    processing_config = pdf_config.get("processing", {})
    
    click.echo(f"Code formatting: {'✅ Enabled' if converter_config.get('format_code_blocks') else '❌ Disabled'}")
    click.echo(f"GPU acceleration: {'✅ Preferred' if converter_config.get('prefer_gpu') else '❌ CPU Only'}")
    click.echo(f"Log level: {converter_config.get('log_level', 'INFO')}")
    click.echo(f"Markdown Output: {output_config.get('output_dir', 'output/markdown')}")
    click.echo(f"Timeout: {processing_config.get('timeout', 300)}s")
    click.echo(f"Max file size: {processing_config.get('max_file_size_mb', 100)}MB")
    
    # Show GPU info if available
    try:
        config_prefer_gpu = converter_config.get("prefer_gpu", True)
        prefer_gpu = config_prefer_gpu and not ctx.obj['cpu_only']
        converter = PDFToMarkdownConverter(prefer_gpu=prefer_gpu)
        
        click.echo(f"\n🖥️  SYSTEM INFORMATION:")
        click.echo(f"Detected device: {converter.device}")
        
        try:
            import torch
            if torch.cuda.is_available():
                click.echo(f"CUDA available: ✅ Yes")
                click.echo(f"GPU devices: {torch.cuda.device_count()}")
                click.echo(f"Primary GPU: {torch.cuda.get_device_name(0)}")
            else:
                click.echo(f"CUDA available: ❌ No")
        except ImportError:
            click.echo(f"PyTorch: ❌ Not installed")
            
    except Exception as e:
        click.echo(f"⚠️  Could not initialize converter: {e}")


if __name__ == "__main__":
    cli()