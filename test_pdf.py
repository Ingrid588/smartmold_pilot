#!/usr/bin/env python3
"""
PDF Generation Test Script
测试 Python 环境是否能够生成 PDF
"""

import traceback
import warnings
import os


# Keep test output clean across environments
warnings.filterwarnings('ignore', category=DeprecationWarning)

def test_weasyprint():
    """测试 WeasyPrint PDF 生成"""
    print("=" * 50)
    print("测试 WeasyPrint PDF 生成")
    print("=" * 50)
    
    try:
        from weasyprint import HTML
        print("✅ WeasyPrint 导入成功")
        
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>PDF Test</title>
        </head>
        <body>
            <h1>Hello World</h1>
            <p>这是 PDF 测试</p>
            <p>如果你能看到这个文件，说明 PDF 生成成功！</p>
        </body>
        </html>
        """
        
        html = HTML(string=html_content)
        html.write_pdf('debug_report.pdf')
        
        print("✅ Success! PDF 已保存为 debug_report.pdf")
        return True
        
    except Exception as e:
        print(f"❌ WeasyPrint 失败: {e}")
        # Print full trace only when explicitly requested (to keep logs clean)
        if os.getenv('PDF_TEST_VERBOSE', '').lower() in ('1', 'true', 'yes'):
            print("\n完整错误信息:")
            traceback.print_exc()
        return False


def test_reportlab():
    """测试 ReportLab PDF 生成 (备选方案)"""
    print("\n" + "=" * 50)
    print("测试 ReportLab PDF 生成 (备选方案)")
    print("=" * 50)
    
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        
        print("✅ ReportLab 导入成功")
        
        c = canvas.Canvas("debug_report_reportlab.pdf", pagesize=A4)
        c.setFont("Helvetica", 24)
        c.drawString(100, 750, "Hello World")
        c.setFont("Helvetica", 12)
        c.drawString(100, 700, "This is a PDF test (ReportLab)")
        c.save()
        
        print("✅ Success! PDF 已保存为 debug_report_reportlab.pdf")
        return True
        
    except ImportError:
        print("⚠️ ReportLab 未安装，跳过测试")
        print("   安装命令: pip install reportlab")
        return False
    except Exception as e:
        print(f"❌ ReportLab 失败: {e}")
        traceback.print_exc()
        return False


def test_fpdf():
    """测试 FPDF PDF 生成 (备选方案)"""
    print("\n" + "=" * 50)
    print("测试 FPDF PDF 生成 (备选方案)")
    print("=" * 50)
    
    try:
        from fpdf import FPDF
        
        print("✅ FPDF 导入成功")
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=24)
        pdf.cell(200, 10, text="Hello World", align='C', new_x='LMARGIN', new_y='NEXT')
        pdf.set_font("Helvetica", size=12)
        pdf.cell(200, 10, text="This is a PDF test (FPDF)", align='C', new_x='LMARGIN', new_y='NEXT')
        pdf.output("debug_report_fpdf.pdf")
        
        print("✅ Success! PDF 已保存为 debug_report_fpdf.pdf")
        return True
        
    except ImportError:
        print("⚠️ FPDF 未安装，跳过测试")
        print("   安装命令: pip install fpdf2")
        return False
    except Exception as e:
        print(f"❌ FPDF 失败: {e}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n🔍 开始测试 PDF 生成能力...\n")
    
    results = {
        "WeasyPrint": test_weasyprint(),
        "ReportLab": test_reportlab(),
        "FPDF": test_fpdf(),
    }
    
    print("\n" + "=" * 50)
    print("测试结果汇总")
    print("=" * 50)
    
    for lib, success in results.items():
        status = "✅ 可用" if success else "❌ 不可用"
        print(f"  {lib}: {status}")
    
    available = [lib for lib, success in results.items() if success]
    if available:
        print(f"\n💡 建议使用: {available[0]}")
    else:
        print("\n⚠️ 没有可用的 PDF 库，请安装:")
        print("   pip install fpdf2  (最简单，无系统依赖)")
        print("   pip install reportlab  (功能强大)")
