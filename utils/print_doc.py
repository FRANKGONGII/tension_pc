import os

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

def print_doc():
    from docx import Document
    from docx.shared import Inches, Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    # 创建文档
    doc = Document()

    # 添加公司名和标题（居中）
    doc.add_paragraph("江苏慧通管道设备有限公司", style='Title').alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph("JiangShu Huitong Pipeline Equipment Co.Ltd").alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph("恒力吊架性能试验记录", style='Heading 1').alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph("Constant Hanger Performance Test Record").alignment = WD_ALIGN_PARAGRAPH.CENTER

    # 添加基本信息表格
    table1 = doc.add_table(rows=2, cols=8)
    table1.style = 'Table Grid'

    table1.rows[0].cells[0].text = "用户\nCustomer"
    table1.rows[0].cells[1].text = ""  # 用户值
    table1.rows[0].cells[2].text = "规格型号\nDescription and type"
    table1.rows[0].cells[3].text = "129235"
    table1.rows[0].cells[4].text = "试验日期\nTest Date"
    table1.rows[0].cells[5].text = "2025年05月09日"
    table1.rows[0].cells[6].text = "吊点代号\nHanger Number"
    table1.rows[0].cells[7].text = "J1155-15-2915"

    # 第二行内容
    table1.rows[1].cells[0].text = "总位移\nTotal travel"
    table1.rows[1].cells[1].text = "123mm"
    table1.rows[1].cells[2].text = "工作载荷\nWorking Load"
    table1.rows[1].cells[3].text = "51.698kN"
    table1.rows[1].cells[4].text = "出厂编号\nSerial Number"
    table1.rows[1].cells[5].text = "H3-192-1"
    table1.rows[1].cells[6].text = "位移方向\nTravel direction"
    table1.rows[1].cells[7].text = "↓"

    format_table_cells(table1)

    # 添加空行替代曲线图区域
    doc.add_paragraph("图片位置")
    doc.add_picture('./resources/png.png', width=Inches(6))  # 你可以调整大小

    # 创建主表格：3行6列
    table2 = doc.add_table(rows=4, cols=6)
    table2.style = 'Table Grid'

    # 第一行（嵌套子表格前的正常填充）
    table2.cell(0, 0).text = "操作员\nOperator"
    table2.cell(0, 1).text = "刘云佳"
    table2.cell(0, 2).text = "实测力值\nActual load"

    # 嵌套子表格：插入到(0,3)
    nested_cell = table2.cell(0, 3)
    nested_table = nested_cell.tables[0] if nested_cell.tables else nested_cell.add_table(rows=2, cols=2)
    nested_table.style = 'Table Grid'
    nested_table.cell(0, 0).text = "Pmax"
    nested_table.cell(0, 1).text = "Pmin"
    nested_table.cell(1, 0).text = "54N"
    nested_table.cell(1, 1).text = "54N"

    # 第一行剩余列
    table2.cell(0, 4).text = "检验员"
    table2.cell(0, 5).text = "陈广春"

    # 第二行
    table2.cell(1, 0).text = "位移起始点值\nInitial point"
    table2.cell(1, 1).text = "188mm"
    table2.cell(1, 2).text = "位移终止点值\nFinishing point"
    table2.cell(1, 3).text = "312mm"
    table2.cell(1, 4).text = "实测位移值\nActual travel"
    table2.cell(1, 5).text = "124mm"

    # 第三行
    table2.cell(2, 0).text = "超载实验值\nOverload\ntest data"
    table2.cell(2, 1).text = "51.386N"
    table2.cell(2, 2).text = "超载起始-终止时间\ntime of\nstarting-finishing"
    table2.cell(2, 3).text = "16:00:00-18:00:00"
    table2.cell(2, 4).text = "超载实验保持时间\nDuration within\noverload test"
    table2.cell(2, 5).text = "5min13s"

    # 第四行
    table2.cell(3, 0).text = "恒定度\nConstant rate"
    table2.cell(3, 1).text = "5.07%"
    table2.cell(3, 2).text = ("载荷偏差度\nLoad tolerance")
    table2.cell(3, 3).text = "0.91%"
    table2.cell(3, 4).text = ("测试结果\nTest result")
    table2.cell(3, 5).text = "合格"

    # 设置主表与嵌套表样式
    format_table_cells(table2, font_size=10)
    format_table_cells(nested_table, font_size=10)

    # 保存 Word 文件
    doc.save("恒力吊架性能试验记录1.docx")

    import win32com.client

    def print_word_file(path):
        word = win32com.client.Dispatch("Word.Application")
        word.ActivePrinter = "EPSON4D76BB (L4160 Series)"
        doc = word.Documents.Open(path)
        doc.PrintOut()  # 打印
        # ActivePrinter="EPSON4D76BB (L4160 Series)"
        doc.Close(False)
        word.Quit()



    print_word_file(os.getcwd() + "/恒力吊架性能试验记录1.docx")


def format_table_cells(table, font_size=9):
    for row in table.rows:
        for cell in row.cells:
            # 设置垂直居中
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

            for paragraph in cell.paragraphs:
                # 设置水平居中
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in paragraph.runs:
                    run.font.size = Pt(font_size)


import pypandoc

def convert_docx_to_pdf(input_path, output_path):
    output = pypandoc.convert_file(input_path, 'pdf', outputfile=output_path)
    return output_path if output == "" else None


if __name__ == '__main__':
    # pdf_path = convert_docx_to_pdf("恒力吊架性能试验记录（无图）.docx", "output.pdf")
    # print("转换成功：" + pdf_path)
    print_doc()
