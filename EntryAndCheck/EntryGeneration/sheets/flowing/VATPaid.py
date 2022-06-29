# -*- encoding: UTF-8 -*-

from sheets.Elements import AccountClass, BaseInfo, ValueAddedTaxInfo


class VATPaid(AccountClass, BaseInfo, ValueAddedTaxInfo, ):
    """已付增值税"""
    inner2outer_map = {
        'product': '产品', 'date': '日期', 'institution': '机构',
        'account_name': '科目', 'account_code': '科目编号',
        'vat': '已交增值税', 'building_tax': '已交城建税', 'education_surcharge': '已交教育费附加',
        'local_education_surcharge': '已交地方教育费附加', 'total_tax': '已交税金',
    }

    # 已在 BankFlow 中产生分录凭证 银行流水中会显示增值税支付

    # def __init__(self, product: str = '', date: datetime.date = None, institution: str = '',
    #              account_code: int = None, account_name: str = '',
    #              vat: float = None, building_tax: float = None, education_surcharge: float = None,
    #              local_education_surcharge: float = None, total_tax: float = None, ):
    #     AccountClass.__init__(self, account_code=account_code, account_name=account_name)
    #     Flowing.__init__(self, product=product, institution=institution, date=date)
    #     ValueAddedTax.init_property(self, vat=vat, building_tax=building_tax, education_surcharge=education_surcharge,
    #                            local_education_surcharge=local_education_surcharge, total_tax=total_tax)
