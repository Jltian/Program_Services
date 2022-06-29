# coding: utf8
import base64
import re
import poplib
import pickle

from email.message import Message
from email.parser import Parser

def decode_base64(s, charset='utf8'):
    return str(base64.decodebytes(s.encode(charset)), encoding=charset)

# 邮箱个人信息
useraccount = 'gzzy@jiumingfunds.com'
password = 'Guzhijm3389'
# 邮件服务器地址
# pop3_server = 'pop.126.com'
pop3_server = 'pop.exmail.qq.com'

# 开始连接到服务器
server = poplib.POP3(pop3_server)
# 可选项： 打开或者关闭调试信息，1为打开，会在控制台打印客户端与服务器的交互信息
server.set_debuglevel(1)
# 可选项： 打印POP3服务器的欢迎文字，验证是否正确连接到了邮件服务器
print(server.getwelcome().decode('utf8'))

# 开始进行身份验证
server.user(useraccount)
server.pass_(password)

# 返回邮件总数目和占用服务器的空间大小（字节数）， 通过stat()方法即可
print("Mail counts: {0}, Storage Size: {0}".format(server.stat()))
# 使用list()返回所有邮件的编号，默认为字节类型的串
resp, mails, octets = server.list()
# print("响应信息： ", resp)
# print("所有邮件简要信息： ", mails)
# print("list方法返回数据大小（字节）： ", octets)

# 下面单纯获取最新的一封邮件
total_mail_numbers = len(mails)
# 默认下标越大，邮件越新，所以total_mail_numbers代表最新的那封邮件
response_status, mail_message_lines, octets = server.retr(total_mail_numbers)
print('邮件获取状态： {}'.format(response_status))
# print('原始邮件数据:\n{}'.format(mail_message_lines))
print('该封邮件所占字节大小: {}'.format(octets))
msg_content = b'\r\n'.join(mail_message_lines)
charset_list = re.findall(re.compile('charset="(.*)"'), msg_content.decode('gb18030'))
if len(charset_list) == 0:
    charset = 'utf-8'
elif len(charset_list) == 1:
    charset = charset_list[0]
else:
    raise RuntimeError(str(charset_list))
msg_content = msg_content.decode(charset)
msg_data = Parser().parsestr(text=msg_content)
# print('解码后的邮件信息:\n{}'.format(msg_data))
assert isinstance(msg_data, Message)
f = open(r'C:\Users\Administrator.SC-201606081350\Downloads\test\test.txt', 'w', encoding=charset)
f.write(msg_data.as_string())
f.close()


# 获取发件人详情
from_str = msg_data.get('From')

print("原生FROM信息：\n" + from_str)

# nickname, account = from_str.split(" ")
# # 获取字串的编码信息
# charset = nickname.split('?')[1]
# # print('编码：{}'.format(charset))
# nickname = nickname.split('?')[3]
# nickname = str(base64.decodebytes(nickname.encode(encoding=charset)), encoding=charset)
# account = account.lstrip('<')
# account = account.rstrip('>')

# 获取收件人详情
to_str = msg_data.get('To')

print("原生To信息：\n" + to_str)

subject = msg_data.get('Subject')
print("原生Subject信息：\n" + subject)

# maildetails.subject = decode_base64(subject.split("?")[3], charset=subject.split("?")[1])
# 获取时间信息，也即是邮件被服务器收到的时间
received_time = msg_data.get("Date")

print(received_time)
# maildetails.receivedtime = received_time

parts = msg_data.get_payload()

print(type(parts))
# print('8'*9, parts[0].as_string())
content_type = parts[0].get_content_type()
print(type(parts[0]), content_type)

index = 1
for msg_parts in parts:
    print('msg_part{}'.format(index))
    index += 1
    assert isinstance(msg_parts, Message)

    print(msg_parts.get_filename())
    print(msg_parts.get_content_maintype())
    print(msg_parts.get_content_subtype())
# print(parts[0])
# content_charset = parts[0].get_content_charset()
# # parts[0] 默认为文本信息，而parts[1]默认为添加了HTML代码的数据信息
# content = parts[0].as_string().split('base64')[-1]
# print('Content*********', decode_base64(content, content_charset))
# content = parts[1].as_string().split('base64')[-1]
# print('HTML Content:', decode_base64(content, content_charset))

# 关闭与服务器的连接，释放资源
server.close()
