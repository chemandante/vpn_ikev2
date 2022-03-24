## Установка и настройка сервера

В статье приводится описание установки на дистрибутив Linux Debian 11. Некоторые действия автоматизируются 
shell-скриптами и скриптами на Python. Если появится желание узнать тему глубже, добро пожаловать в [оригинальную 
статью](https://vc.ru/dev/66942-sozdaem-svoy-vpn-server-poshagovaya-instrukciya) на базе которой и создавались скрипты. 

### 1. Обновление Debian

Обновим индекс пакетов в репозиториях, возможно, есть обновления:

```
apt update
```

Установим эти обновления:

```
apt upgrade
```

### 2. Установка strongSwan и дополнительных компонентов

Для установки используем команду:

```
apt install strongswan
```

Для того чтобы создавать сертификаты для аутентификации сервера и клиентов, потребуется пакет strongswan-pki. Установим 
его:

```
apt install strongswan-pki
```

iptables — это утилита, которая управляет встроенным в Linux файрволом netfilter. Для того чтобы сохранять правила
iptables в файле и подгружать их при каждом запуске системы, установим пакет iptables-persistent:

```
apt install iptables-persistent
```

После установки нас спросят, сохранить ли текущие правила IPv4 и IPv6. Ответим «Нет», так как у нас новая система, и по сути нечего сохранять.

Если планируется использование клиентов iOS/macOS, понадобится установка компонента `zsh` на сервере:

```
apt install zsh
```

### 3. Установка vpn_ike2

Скачиваем скрипты этого проекта, например, в домашнюю директорию.

```
git clone --depth 1 https://github.com/chemandante/vpn_ikev2
cd vpn_ikev2
```

Если git отсутствует, а на чистом сервере он отсутствует, то предварительно установим его, а потом повторим 
предыдущий пункт:

```
apt install git
```

Если скрипты скачали каким-то иным способом, то не забываем дать им разрешение на исполнение:

```
chmod +x *.py
chmod +x *.sh
```

### 4. Настройка сервера скриптом

Предварительно настроим конфигурацию будущего сервера, которая хранится в `config.json`, например, с помощью nano:

```
nano config.json
```

Нас интересуют три поля:

`serverName` — имя VPN-сервера (в прилагаемом файле имя `oscar`)  
`serverAddr` — адрес сервера, по которому он будет доступен (в примере `oscar.domain.com`)  
`ipSubnet` — адрес и маска подсети наших будущих туннелей (в примере `10.0.0.0/24`)

Редактируем, подставляем свои значения. Они будут многократно использованы в процессе настройки сервера и генерации 
ключей для клиентов. В дальнейшем в статье будут использоваться те значения, которые уже прописаны в прилагаемом 
файле.

Запускаем скрипт настройки сервера:
```
./setup.server.py
```

В первую очередь будут созданы корневой ключ и сертификат, он же “CA” (Certificate Authority), который выпустит нам 
остальные сертификаты. Он будет создан в файлах `ca.pem`: ключ в `/etc/ipsec.d/private/`,
сертификат в `/etc/ipsec.d/cacerts/`.

Если оба файла уже присутствовали на сервере, то скрипт спросит, требуется ли их перегенерация (отвечаем честно):

```
CA root certificate already exists. Would you like to regenerate CA key? [y/N]
```

В случае успешной генерации появится:
```
Generating CA root certificate for 'oscar.domain.com'...
Done
```

Затем создается ключ и сертификат VPN-сервера, требуемый для аутентификации соединения. Аналогичным образом, если 
ключ и сертификат уже готовы, возникнет вопрос о перегенерации:  
```
Server private key for 'oscar' already exists. Would you like to regenerate key? [y/N]
```

Так же, в случае успешной генерации сообщение:
```
Generating server certificate for 'oscar.domain.com'...
Done
```

Если все прошло нормально, то получим 4 файла:  
`/etc/ipsec.d/cacerts/ca.pem` — сертификат CA (самоподписанный);  
`/etc/ipsec.d/private/ca.pem` — закрытый ключ CA;  
`/etc/ipsec.d/certs/oscar.pem` — сертификат сервера;  
`/etc/ipsec.d/private/oscar.pem` — закрытый ключ сервера.

Далее скрипт создает файлы конфигурации сервера `/etc/ipsec.conf` и `/etc/ipsec.secrets`, а также, перезапускает 
службу `ipsec`, предварительно спросив разрешения на это:

```
Would you like to make 'ipsec.conf' and 'ipsec.secrets'? [Y/n]
```

Прежние файлы `/etc/ipsec.conf` и `/etc/ipsec.secrets` будут потеряны, если согласиться на создание новых.

Если всё хорошо, то сервер запустится:

```
Starting strongSwan 5.9.1 IPsec [starter]...
```

Если упадет в ошибку, то можно посмотреть, что именно произошло, почитав системный лог. Команда выведет 50 последних строк лога:
```
tail -n 50 > /var/log/syslog
```

На этом работа скрипта закончена, но не закончена настройка сервера.

### 5. Настройка сетевых параметров ядра

Теперь нам необходимо внести некоторые изменения в файл `/etc/sysctl.conf`.

```
nano /etc/sysctl.conf
```
Найдем в файле следующие переменные и внесем в них изменения:

```
#Раскомментируем данный параметр, чтобы включить переадресацию пакетов
net.ipv4.ip_forward = 1

#Раскомментируем данный параметр, чтобы предотвратить MITM-атаки
net.ipv4.conf.all.accept_redirects = 0

#Раскомментируем данный параметр, чтобы запретить отправку ICMP-редиректов
net.ipv4.conf.all.send_redirects = 0

#В любом месте файла на новой строке добавим данный параметр, запретив поиск PMTU
net.ipv4.ip_no_pmtu_disc = 1
```

Подгрузим новые значения:

```
sysctl -p
```

Настройка сетевых параметров ядра завершена.

### 6. Настройка iptables

Перейдем к формированию правил iptables. На всякий пожарный, очистим все цепочки:

```
iptables -P INPUT ACCEPT
iptables -P FORWARD ACCEPT
iptables -F
iptables -Z
```

Разрешим соединения по SSH на 22 порту, чтобы не потерять доступ к машине:

```
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
iptables -A INPUT -p tcp --dport 22 -j ACCEPT
```

Разрешим соединения на loopback-интерфейсе:

```
iptables -A INPUT -i lo -j ACCEPT
```

Теперь разрешим входящие IPSec-соединения на UDP-портах 500 и 4500:

```
iptables -A INPUT -p udp --dport  500 -j ACCEPT
iptables -A INPUT -p udp --dport 4500 -j ACCEPT
```

Разрешим переадресацию ESP-трафика:

```
iptables -A FORWARD --match policy --pol ipsec --dir in  --proto esp -s 10.10.10.0/24 -j ACCEPT
iptables -A FORWARD --match policy --pol ipsec --dir out --proto esp -d 10.10.10.0/24 -j ACCEPT
```

Настроим маскирование трафика, так как наш VPN-сервер, по сути, выступает как шлюз между Интернетом и VPN-клиентами:

```
iptables -t nat -A POSTROUTING -s 10.10.10.0/24 -o eth0 -m policy --pol ipsec --dir out -j ACCEPT
iptables -t nat -A POSTROUTING -s 10.10.10.0/24 -o eth0 -j MASQUERADE
```

Обратите внимание на интерфейс `eth0` — в моем случае он был совсем другим. Узнать его можно с помощью команды `ip 
address`

Настроим максимальный размер сегмента пакетов:

```
iptables -t mangle -A FORWARD --match policy --pol ipsec --dir in -s 10.10.10.0/24 -o eth0 -p tcp -m tcp --tcp-flags SYN,RST SYN -m tcpmss --mss 1361:1536 -j TCPMSS --set-mss 1360
```

Запретим все прочие соединения к серверу:

```
iptables -A INPUT -j DROP
iptables -A FORWARD -j DROP
```

Сохраним правила, чтобы они загружались после каждой перезагрузки:

```
netfilter-persistent save
netfilter-persistent reload
```

Настройка iptables завершена.

Перезагрузим машину:

```
reboot
```

### 7. Проверка

Проверяем, работают ли правила iptables:

```
sudo su
iptables -S
```
Должны получить:

```
-P INPUT ACCEPT
-P FORWARD ACCEPT
-P OUTPUT ACCEPT
-A INPUT -m state --state RELATED,ESTABLISHED -j ACCEPT
-A INPUT -p tcp -m tcp --dport 22 -j ACCEPT
-A INPUT -i lo -j ACCEPT
-A INPUT -p udp -m udp --dport 500 -j ACCEPT
-A INPUT -p udp -m udp --dport 4500 -j ACCEPT
-A INPUT -j DROP
-A FORWARD -s 10.10.10.0/24 -m policy --dir in --pol ipsec --proto esp -j ACCEPT
-A FORWARD -d 10.10.10.0/24 -m policy --dir out --pol ipsec --proto esp -j ACCEPT
-A FORWARD -j DROP
```

Работает ли strongSwan:

```
ipsec statusall
```

```
Status of IKE charon daemon (strongSwan 5.5.1, Linux 4.9.0-8-amd64, x86_64):
  uptime: 71 seconds, since Jan 23 23:22:16 2019

...
```
Всё должно работать.

### 8. Уборка

Во-первых, закрытые ключи клиентов на сервере не нужны - после создания профилей клиентских устройств (iOS/mscOS) 
или сертификатов (Windows) эти ключи надо удалить. Они находятся в папке `/etc/ipsec.d/private`. По-умолчанию, 
скрипт генерации клиентских сертификатов `gen_client_key.py` удаляет эти ключи автоматически.

Во-вторых, если не планируется больше выпускать клиентские сертификаты, то можно удалить и закрытый корневой ключ 
удостоверяющего центра (CA) (`/etc/ipsec.d/private/ca.pem`).

**Важно!** Не удалите закрытый ключ сервера из этой же папки (в нашем примере `oscar.pem`) — он необходим!

### 9. Создание ключей и сертификатов клиентов

Процесс создания сертификата и профиля устройства тут: [Настройка клиента iOS/macOS](ios.html)

Процесс создания сертификата и скрипта настройки тут: [Настройка клиента Windows](win.html)

### 10. Разные тонкости

#### Подсоединение нескольких клиентов по одному сертификату

Если есть желание разрешить подсоединение нескольких клиентов по одному сертификату (ну, мало ли), то в файле 
`/etc/ipsec.conf` строку `uniqueids=keep` надо заменить на `uniqueids=never`
