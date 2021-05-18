# coding=utf-8
import os
import sys
import xlwt

#https://blog.csdn.net/weixin_41140174/article/details/90897996
#Application-->Workbook-->Worksheet-->Range/Cell-->Row/Column

file_path = sys.path[0]+'\\00_file_name_list.xls' #sys.path[0]为要获取当前路径，00_file_name_list.xls为要写入的文件
new_workbook = xlwt.Workbook(encoding = 'utf-8', style_compression = 0) #新建一个excel
new_sheet = new_workbook.add_sheet('file_name') #新建一个sheet
path_dir = os.listdir(sys.path[0]) #文件放置在当前文件夹中，用来获取当前文件夹内所有文件目录

#将文件列表写入test.xls
i = 0
for s in path_dir:
    new_sheet.write(i,0,s) #参数i,0,s分别代表行，列，写入值
    i = i + 1

print(file_path)
print(i) #显示文件名数量
new_workbook.save(file_path)
