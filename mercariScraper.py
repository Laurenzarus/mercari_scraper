import requests
from bs4 import BeautifulSoup
import urllib.parse
import argparse
import csv
# import selenium from webdriver
print('successfully imported packages')

useUrl = False
useKeywords = False

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.4 Safari/605.1.15"
MERCARI_BASE = "https://www.mercari.com/search/?keyword="

def init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        usage='%(prog)s [OPTION] [FILE]...',
        description='Collect data on Mercari products by providing a URL or search String.'
    )
    parser.add_argument('-u', '--url', help="The url of the Mercari search results to parse")
    parser.add_argument('-s', '--searchstring', help="The search string to enter into Mercari's search bar")
    parser.add_argument('-l', '--limit', help='The upper limit on how many entries should be searched')
    parser.add_argument('-w', '--write', help='The filename to write out to (if applicable)')
    return parser


def construct_url(searchstr):
    return (MERCARI_BASE + urllib.parse.quote(searchstr))

def validateArgs(args):
    print('validating arguments!')
    if args.url != None and args.searchstring != None:
        raise ValueError('Please do not provide both a searchstring and url value.')
    if args.url != None:
        global useUrl
        useUrl = True
    elif args.searchstring != None:
        global useKeywords
        useKeywords = True

def getPageData(args) -> requests.Response:
    print(args)
    # initialize headers
    reqHeaders = { 'User-Agent': USER_AGENT }
    # create user-agent
    if useUrl:
        print('trying to get url')
        return requests.get(args.url, headers=reqHeaders)
    elif useKeywords:
        print(construct_url(args.searchstring))
        return requests.get(construct_url(args.searchstring),  headers=reqHeaders)
        

def writeCsv(dataArr):
    f = open('./output.csv', 'w')
    writer = csv.writer(f)
    header = ['Item Name', 'Item Price', 'Discount Price (if applicable)', 'Size', 'URL' ]
    csvRows = organizeData(dataArr) 
    writer.writerow(header)
    writer.writerows(csvRows)
    f.close()

def organizeData(dataArr):
    rows = []
    for entry in dataArr:
        rowData = []
        rowData.append(entry['name'] if entry['name'] != None else '')
        rowData.append(entry['itemPrice'] if entry['itemPrice'] != None else '')
        rowData.append(entry['discountPrice'] if entry['discountPrice'] != None else '')
        rowData.append(entry['size'] if entry['size'] != None else '')
        rowData.append(entry['url'] if entry['url'] != None else '')
        rows.append(rowData)
    return rows 
    
def create_data_dict(bsMatches): 
    itemInfoLst = []
    for bsMatch in bsMatches:
        itemName = bsMatch.find(attrs={'data-testid' : 'ItemName'}).string
        itemUrl = None
        itemUrl = bsMatch['href']
        itemUrl = 'mercari.com' + itemUrl
        itemPrice = None
        discountPrice = None
        itemPriceTag = bsMatch.find(attrs={'data-testid' : 'ItemPrice'})
        if itemPriceTag.string == None:
            # has a discount price and normal price
            discountPrice = itemPriceTag.find(class_='withMetaInfo__DiscountPrice-sc-1j2k5ln-10 TPGYL').string
            itemPrice = itemPriceTag.find(class_='withMetaInfo__OriginalPrice-sc-1j2k5ln-12 dRCDAZ').string
        else:
            itemPrice = itemPriceTag.string
        itemSizeTag = bsMatch.find(attrs={'data-testid' : 'ItemSize'})
        itemSize = None
        if itemSizeTag != None:
            itemSize = itemSizeTag.string
        itemInfo = { 'name' : itemName }
        itemInfo['itemPrice'] = itemPrice
        itemInfo['discountPrice'] = discountPrice
        itemInfo['size'] = itemSize
        itemInfo['url'] = itemUrl
        itemInfoLst.append(itemInfo)
    return itemInfoLst

def main():
    parser = init_argparse()
    args = parser.parse_args()
    validateArgs(args)
    res = getPageData(args)
    print('successful retrieve ' + str(res.status_code == requests.codes.ok))
    bs = BeautifulSoup(res.content, 'html.parser')
    itemMatches = bs.find_all('a', class_="Text__LinkText-sc-1e98qiv-0-a Link__StyledAnchor-dkjuk2-0 fiIUU Link__StyledPlainLink-dkjuk2-3 beSDvJ")
    itemInfoLst = create_data_dict(itemMatches)
    print('List of items has size of ' + str(len(itemInfoLst)))
    writeCsv(itemInfoLst)

if __name__ == "__main__":
    main()
