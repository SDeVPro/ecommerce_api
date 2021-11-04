from PyPDF2 import PdfFileWriter, PdfFileReader
import os 

PWD = "/Users/admin/Desctop/API_ENV/ecommerce/pdf_files"

def write_new_pdf(filename,data={}):
    path = os.path.join(PWD+"/"+str(filename)+".pdf")
    if data:
        with open(path,"a+",encoding="utf-8") as pdf:
            for key,value in data.items():
                pdf.write(key+":"+value+"\n")
    else:
        print("sorry No Data")
n = {"thomas":"3","adel":"5","saeed":"10"}
write_new_pdf("example",n)
