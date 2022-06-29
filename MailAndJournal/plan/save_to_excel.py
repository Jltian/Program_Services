
import pandas as pd




def tosheet(path, flow):
    writer = pd.ExcelWriter(path)
    ind = 0
    start = 0
    name = set()
    while ind <= len(flow) - 1:
        if str(flow['日期'][ind]) not in name:
            name.add(str(flow['日期'][ind]))
            # print(name, ind)
        while str(flow['日期'][ind]) in name:
            ind += 1
            if ind == len(flow):
                break
        if start <= len(flow)-1:
            df = flow[start:ind]
            # print(start, ind)
            df.to_excel(writer, sheet_name=str(flow['日期'][start]), index=False, startrow=1)
        start = ind
        # print(start, ind)
    # for ind in range(len(flow)):
    #     print(2, start, ind)
    #     if ind < len(flow) - 1:
    #         if str(flow['日期'][ind]) not in name:
    #             name.append(str(flow['日期'][ind]))
    #             # print(ind,)
    #         while str(flow['日期'][ind]) in name:
    #             if ind < len(flow) - 1:
    #                 ind += 1
    #             else:
    #                 ind += 1
    #                 break
    #
    #     # if start == len(flow) - 1:
    #     #     if str(flow['日期'][ind]) in name:
    #     #         ind += 1
    #     #         print(0, start, ind)
    #     #     else:
    #     #         start = len(flow)-1
    #     #         ind += 1
    #     #         print(2, start, ind)
    #     print(start, ind)
    #     if start < len(flow):
    #         df = flow[start:ind]
    #         print(1, start, ind)
    #         df.to_excel(writer, sheet_name=str(flow['日期'][start]), index=False, startrow=1)
    #     start = ind


    writer.save()
    writer.close()



