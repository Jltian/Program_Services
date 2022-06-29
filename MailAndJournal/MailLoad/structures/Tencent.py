# -*- encoding: UTF-8 -*-
import re

from email import message_from_bytes, message_from_string
from email.message import Message
from email.utils import parseaddr, parsedate_to_datetime

from jetend.structures import decode_email_str


def parse_tencent_email_content_part(msg_part: Message):
    result_list = list()
    if msg_part.is_multipart():  # 如果邮件对象是一个MIMEMultipart, 内容带附件
        for sub_msg_part in msg_part.get_payload():
            assert isinstance(sub_msg_part, Message), '{} {}'.format(type(sub_msg_part), sub_msg_part)
            result_list.extend(parse_tencent_email_content_part(sub_msg_part))
    else:

        new_part_obj = dict()
        new_part_obj['content_type'] = msg_part.get_content_type()
        content_main_type, content_sub_type = new_part_obj['content_type'].split('/')
        content_disposition = msg_part.get_content_disposition()
        new_part_obj['content_disposition'] = content_disposition
        new_part_obj['charset'] = msg_part.get_content_charset()
        if content_disposition is None:   # 非附件
            if content_main_type == 'text':         # 处理文本内容
                try:
                    new_part_obj['data'] = msg_part.get_payload(decode=True).strip().decode(new_part_obj['charset'])
                except TypeError:
                    new_part_obj['data'] = ''
                except UnicodeDecodeError:
                    new_part_obj['data'] = ''
            elif content_main_type == 'image':
                new_part_obj['data'] = msg_part.get_payload(decode=True)
            elif content_main_type == 'application':
                try:
                    new_part_obj['name'] = decode_email_str(msg_part.get_filename()).replace('\r', '').replace('\n', '')
                except AttributeError:
                    from datetime import datetime
                    new_part_obj['name'] = 'unknown{}'.format(datetime.now())
                new_part_obj['data'] = msg_part.get_payload(decode=True)
            else:
                raise NotImplementedError('{}\n{}'.format(content_main_type, msg_part.as_string()))

        elif content_disposition == 'attachment':
            new_part_obj['name'] = decode_email_str(msg_part.get_filename()).replace('\r', '').replace('\n', '')
            assert new_part_obj['name'] is not None, msg_part.as_string()
            if content_main_type == 'application':            # 处理附件
                new_part_obj['data'] = msg_part.get_payload(decode=True)
            elif content_main_type == 'text':
                new_part_obj['data'] = msg_part.get_payload(decode=True)
            elif content_main_type == 'image':
                new_part_obj['data'] = msg_part.get_payload(decode=True)
            elif content_main_type == 'content':
                new_part_obj['data'] = msg_part.get_payload(decode=True)
            else:
                raise NotImplementedError('{} {}\n{}'.format(
                    content_disposition, content_main_type, msg_part.as_string()
                ))
            # o = open(r'C:\Users\Administrator.SC-201606081350\Downloads\test\{}'.format(new_part_obj['name']), 'wb')
            # o.write(new_part_obj['data'])
            # o.close()

        elif content_disposition == 'inline':

            if content_main_type == 'text':  # 处理文本内容
                new_part_obj['charset'] = msg_part.get_content_charset()
                try:
                    new_part_obj['data'] = msg_part.get_payload(decode=True).strip().decode(new_part_obj['charset'])
                except TypeError:
                    new_part_obj['data'] = ''
            elif content_main_type == 'application':
                pass
            elif content_main_type == 'image':
                pass
            else:
                raise NotImplementedError('{}\n{}'.format(content_main_type, msg_part.as_string()))

        else:
            raise NotImplementedError('{}\n{}'.format(content_disposition, msg_part.as_string()))
        result_list.append(new_part_obj)
    return result_list


def decode_email_bytes(msg_byte: bytes):
    charset_list = re.findall(re.compile('charset="(.*)"'), msg_byte.decode('gb18030', errors='ignore'))
    if len(charset_list) >= 1:
        charset = charset_list[0]
    else:
        charset_list = re.findall(re.compile('charset="(.*)"'), msg_byte.decode('utf-8', errors='ignore'))
        if len(charset_list) >= 1:
            charset = charset_list[0]
        else:
            raise NotImplementedError(message_from_bytes(msg_byte).as_string())
    return msg_byte.decode(charset)


def parse_tencent_email_details(data: bytes):
    """
    返回解析后的字典 {
        'from_nickname': 发件人名称,
    }
    :param data:
    :return: dict
    """
    msg_data = message_from_bytes(data)
    assert isinstance(msg_data, Message), str(msg_data)

    new_obj = dict()

    msg_str = msg_data.get_charset()
    if msg_str is None:
        try:
            charset_list = re.findall(re.compile('charset=(.*)\n'), msg_data.as_string())
            if len(charset_list) >= 1:
                msg_str = charset_list[0]
            else:
                charset_list = re.findall(re.compile('=\?(\w*)\?'), msg_data.as_string())
                if len(charset_list) >= 1:
                    msg_str = charset_list[0]
                else:
                    msg_str = None
                    for encoding_tag in ('gb18030', 'utf-8', 'gb2312','GBK'):
                        try:
                            data.decode(encoding=encoding_tag)
                            msg_str = encoding_tag
                        except UnicodeDecodeError:
                            continue
                    assert msg_str is not None, '未能识别邮件内容编码\n{}'.format(msg_data.as_string())
                # msg_str = msg_data.get('Subject')
                # if '?' in msg_str:
                #     msg_str = msg_str.split('?')[1]
                # else:
                #     if msg_data.is_multipart():
                #             if sub_msg_data
                #     else:
                #         raise RuntimeError(msg_data.as_string())
            try:
                #msg_data = message_from_string(data.decode(encoding=msg_str))
                msg_data = message_from_string(data.decode(msg_str,'ignore'))
            except:
                return {"flag" : "unorder"}
        except KeyError:
            msg_str = msg_data.get('X-QQ-mid')
            if 'recall' in msg_str:
                return {
                    'message_id': None, 'mime_version': None, 'from_account': None, 'from_nickname': None,
                    'to_nickname': None, 'subject': None, 'received_time': None, 'content': list()
                }
            else:
                raise NotImplementedError(msg_data.as_string())
        except UnicodeEncodeError:
            msg_str = decode_email_str(msg_data.get('Subject'))
            if '系统邮件' in msg_str and '拦截' in msg_str:
                return {
                    'message_id': None, 'mime_version': None, 'from_account': None, 'from_nickname': None,
                    'to_nickname': None, 'subject': None, 'received_time': None, 'content': list()
                }
            else:
                raise RuntimeError(msg_data.as_string())
    else:
        raise NotImplementedError(msg_data.as_string())
    new_obj['charset'] = msg_str
    assert isinstance(msg_data, Message), str(msg_data)

    msg_str = msg_data.get('Message-Id')        # 获取邮件编号
    try:
        new_obj['message_id'] = msg_str.strip('<>')
    except AttributeError:
        new_obj['message_id'] = None

    msg_str = msg_data.get('Mime-Version')
    new_obj['mime_version'] = decode_email_str(msg_str)

    msg_str = msg_data.get('From')  # 获取发件人详情
    new_obj['from_nickname'], new_obj['from_account'] = parseaddr(msg_str)
    try:
        new_obj['from_nickname'] = decode_email_str(new_obj['from_nickname'])
    except UnicodeDecodeError:
        pass

    msg_str = msg_data.get('To')  # 获取收件人详情
    new_obj['to_nickname'], new_obj['to_account'] = parseaddr(msg_str)
    new_obj['to_nickname'] = decode_email_str(new_obj['to_nickname'])

    msg_str = msg_data.get('Subject')  # 获取主题信息
    new_obj['subject'] = decode_email_str(msg_str)

    msg_str = msg_data.get("Date")  # 获取时间信息
    new_obj['received_time'] = parsedate_to_datetime(msg_str)

    # print(new_obj)

    new_obj['content'] = parse_tencent_email_content_part(msg_data)
    return new_obj


if __name__ == '__main__':
    for i in range(40, 200, 1):
        print('=' * 20, " {} ".format(i + 1), '=' * 20)
        f = open(r'Z:\NutStore\数据备份文件夹\估值邮箱数据备份\{}.mb'.format(i + 1), 'rb')
        file_content = f.read()
        f.close()
        parse_tencent_email_details(file_content)
