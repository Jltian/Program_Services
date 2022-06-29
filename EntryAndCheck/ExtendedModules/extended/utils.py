# -*- encoding: UTF-8 -*-
# ---------------------------------import------------------------------------
import datetime
import math

from extended.Exceptions import ParamNoContentError


def is_chinese_char(char: str):
    """判断一个字符是否是中文 -> bool"""
    assert len(char) == 1
    if '\u4e00' <= char <= '\u9fff':
        return True
    else:
        return False


def is_english_char(char: str):
    """判断一个字符是否是英文 -> bool"""
    import re
    assert len(char) == 1
    if re.match(r'[a-zA-Z]', char, re.I):
        return True
    else:
        return False


def str_similarity(base_string, compare_string) -> float:
    count = 0
    for i in range(len(compare_string)):
        if compare_string[i] in base_string:
            count += 1
    if len(base_string) > 0:
        return count / len(base_string)
    else:
        return 0.0


def str_check(obj) -> str:
    from decimal import Decimal
    max_decimal = 16
    if obj is None:
        return ''
    elif isinstance(obj, str):
        return obj.strip()
    elif isinstance(obj, float):
        if math.isnan(obj):
            return ''
        if abs(Decimal(str(obj)).as_tuple().exponent) > max_decimal:
            return str(round(obj, max_decimal))
        else:
            return str(float(obj))
    else:
        try:
            return str_check(str(obj))
        except ValueError:
            raise NotImplementedError('got str value {} with type {}'.format(obj, type(obj)))


def is_valid_float(obj) -> bool:
    if isinstance(obj, float):
        return not (math.isnan(obj) or math.isinf(obj))
    elif obj is None:
        return False
    else:
        return is_valid_float(float_check(obj))


def is_valid_int(obj) -> bool:
    if isinstance(obj, int):
        return not (math.isnan(obj) or math.isinf(obj))
    elif obj is None:
        return False
    else:
        return is_valid_int(int_check(obj))


def is_valid_str(obj) -> bool:
    if isinstance(obj, str):
        return obj != ''
    elif obj is None:
        return False
    else:
        return is_valid_str(str_check(obj))


def safe_division(upper, lower, min_error: float = 0.000001) -> float:
    if abs(float_check(lower)) < min_error:
        if abs(float_check(upper)) < min_error:
            return 0
        else:
            raise ZeroDivisionError('{} / {} with min_error {}'.format(upper, lower, min_error))
    else:
        return float_check(upper) / float_check(lower)


def float_check(obj) -> float:
    from decimal import Decimal
    max_decimal = 16
    if obj is None:
        return math.nan
    elif isinstance(obj, str):
        if len(obj) == 0 or obj == 'nan':
            return math.nan
        else:
            return float_check(float(str_check(obj).replace(',', '').replace('HKD', '')))
    elif isinstance(obj, int):
        return float_check(float(obj))
    elif isinstance(obj, float):
        if math.isnan(obj):
            return math.nan
        if abs(Decimal(str(obj)).as_tuple().exponent) > max_decimal:
            return round(obj, max_decimal)
        else:
            return obj
    else:
        try:
            return float_check(float(obj))
        except ValueError:
            raise NotImplementedError('got float value {} with type {}'.format(obj, type(obj)))


def is_different_float(f_1: float, f_2: float, gap: float = 0.01) -> float:
    assert is_valid_float(f_1), '{} {}'.format(f_1, type(f_1))
    assert is_valid_float(f_2), '{} {}'.format(f_2, type(f_2))
    assert is_valid_float(gap), '{} {}'.format(gap, type(gap))
    if abs(f_1 - f_2) >= gap:
        return True
    else:
        return False


def int_check(obj) -> int:
    if obj is None:
        raise ParamNoContentError(str(obj))
    elif isinstance(obj, (str, float)):
        obj = float_check(obj)
        if math.isnan(obj):
            raise ParamNoContentError(str(obj))
        else:
            return int(obj)
    elif isinstance(obj, int):
        return obj
    else:
        try:
            return int_check(int(obj))
        except ValueError:
            raise NotImplementedError('got int value {} with type {}'.format(obj, type(obj)))


def date_check(obj, date_format: str = '%Y-%m-%d') -> datetime.date:
    if obj is None:
        raise ParamNoContentError(str(obj))
    elif isinstance(obj, str):
        obj = str_check(obj)
        if len(obj) == 0:
            raise ParamNoContentError(obj)
        else:
            return datetime.datetime.strptime(obj, date_format).date()
    elif isinstance(obj, datetime.datetime):
        return obj.date()
    # elif isinstance(obj, pd_datetime):
    #     return datetime.date(obj.year, obj.month, obj.day)
    elif isinstance(obj, datetime.date):
        return obj
    else:
        raise NotImplementedError('got date value {} with type {}'.format(obj, type(obj)))


def datetime_check(obj, datetime_format: str = '%Y-%m-%d %H:%M:%S') -> datetime.datetime:
    if obj is None:
        raise ParamNoContentError(obj)
    elif isinstance(obj, str):
        obj = str_check(obj)
        if obj is None:
            raise ParamNoContentError(obj)
        else:
            try:
                return datetime.datetime.strptime(obj, datetime_format)
            except ValueError as va_error:
                print(obj)
                raise va_error
    elif isinstance(obj, datetime.datetime):
        return obj
    # elif isinstance(obj, pd.datetime):
    #     return datetime.datetime(obj.year, obj.month, obj.day, obj.hour, obj.minute, obj.second, obj.microsecond)
    elif isinstance(obj, datetime.date):
        return datetime.datetime.combine(obj, datetime.time())
    else:
        raise NotImplementedError('got date value {} with type {}'.format(obj, type(obj)))


def check_addition_match(
        add_left, add_right, add_result, error_percent: float = 0.01, error_abs: float = 1,
) -> bool:
    assert isinstance(add_left, (int, float, )), type(add_left)
    assert isinstance(add_right, (int, float, )), type(add_right)
    assert isinstance(add_result, (int, float, )), type(add_result)

    result = float(add_left + add_right)
    assert is_valid_float(result), '{} {} {}'.format(add_left, add_right, add_result)
    a_e = abs(result - add_result)
    if abs(add_result) >= 0.01:
        p_e = abs(1 - result / add_result)
    else:
        p_e = None
    if p_e is None:
        return a_e < error_abs
    else:
        return p_e < error_percent


def check_multiply_match(
        multi_left, multi_right, multi_result, error_percent: float = 0.01, error_abs: float = 1,
) -> bool:
    assert isinstance(multi_left, (int, float, )), type(multi_left)
    assert isinstance(multi_right, (int, float, )), type(multi_right)
    assert isinstance(multi_result, (int, float, )), type(multi_result)

    result = float(multi_left * multi_right)
    assert is_valid_float(result), '{} {} {}'.format(multi_left, multi_right, multi_result)
    a_e = abs(result - multi_result)
    if abs(multi_result) >= 1:
        p_e = abs(1 - result / multi_result)
    else:
        p_e = None
    if p_e is None:
        return a_e < error_abs
    else:
        return p_e < error_percent
