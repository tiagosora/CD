# projecto-semestral-102491_104142
projecto-semestral-102491_104142 created by GitHub Classroom

Created by 

- 102491 - Raquel Paradinha 
- 104142 - Tiago Carvalho

------

## Protocolo - Cliente <--> Daemon

| Message            | Sender | Receiver | JSON                                          |
| ------------------ | ------ | -------- | --------------------------------------------- |
| ImgListRequest     |        |          | {"command": "imgList"}                        |
| ImgListResponse    |        |          | {"command": "imgList", "imgList": imgList}    |
| ImgRequestMessage  |        |          | {"command": "search", "imgID": imageID}       |
| ImgResponseMessage |        |          | {"command": "searchResponse", "img": image}   |

ImgListRequest       Pedido da lista de todas as imagens presentes no sistema

ImgListResponse      Resposta com a lista de todas as imagens presentes no sistema

ImgRequestMessage    Pedido para que lhe seja enviada uma imagem do sistema, pelo seu imagehash

ImgResponseMessage   Resposta com parte da imagem pedida. Várias destas mensagens formam a imagem pedida completa


------

## Protocolo - Daemon <--> Daemon

| Message            | Sender | Receiver | JSON                                                 |
| ------------------ | ------ | -------- | ---------------------------------------------------- |
| AckDaemonsMessage  |        |          | {"command": "ackDaemons", "port": port}              | 
| AskConnectMessage  |        |          | {"command": "askConnect"}, "port": port}             | 
| ListDaemonMessage  |        |          | {"command": "listDaemon", "daemonList": daemonList}  |
| UpdateImgMessage   |        |          | {"command": "updateImg, "imgList": imgList}          |
| UpdateResMessage   |        |          | {"command": "updateImgRes", "imgList": imgList}      |
| ImgRequestDaemon   |        |          | {"command": "searchDaemon", "imgID": imageID}        |
| ImgResponseDaemon  |        |          | {"command": "searchDaemonResponse", "img": image}    |

AckDaemonsMessage   Após a conexão com o primeiro Daemon. Envia-lhe esta mensagem com o seu nó.

AskConnectMessage   Mensagem com o seu nó para que o Daemon destinatário se possa conectar ao emissor.

ListDaemonMessage   Mensagem com as portas de todos os Daemons do sistem, enviada para todos os novos Daemons

UpdateImgMessage    Mensagem enviada para os novos Daemons, aquando da conexão, a fim de eles conseguirem dar update ao conjunto de imagens do sistema

UpdateResMessage    Mensagem enviada como resposta à UpdateImgMessage, caso novoo Daemon tenha alterado a lista de imagens do sistema. A mensagem contém essa nova lista,  de modo a que todos os Daemons do sistema sejam notificados

ImgRequestDaemon    Pedido para que lhe seja enviada uma imagem de uma pasta de outro Daemon, pelo seu imagehash

ImgResponseDaemon   Resposta com parte da imagem pedida pelo Daemon de forma a que este possa enviar ao seu cliente.

