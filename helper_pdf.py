'''
Created on 2024年2月24日

@author: lenovo
'''

import time

import pdfkit

def url_to_pdf(url, 
               base_dir,
               path_wkthmltopdf = r'D:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe',
               ):
    config = pdfkit.configuration(wkhtmltopdf=path_wkthmltopdf)
    to_file = str(base_dir / f"{time.time()}.pdf") 
    pdfkit.from_url(url, to_file, configuration=config)
    return to_file

