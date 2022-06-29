import chardet

with open("D:\\Documents\\实习生-金融工程\\Desktop\\48026.mb","rb") as f:
    msg = f.read()
    result = chardet.detect(msg)
    print(result["encoding"])
