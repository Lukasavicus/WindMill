import requests as req
url = "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoDolarDia(dataCotacao=@dataCotacao)?@dataCotacao='07-15-2020'&$top=100&$format=json"
data = req.get(url)
print(data)