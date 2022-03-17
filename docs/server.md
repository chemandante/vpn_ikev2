## Установка и настройка сервера

### 1. Установка strongSwan

Для установки используем команду:

`apt-get install strongswan`

К детальной настройке strongSwan мы вернемся чуть позже, а пока создадим сертификаты, чтобы наши устройства смогли подключиться по VPN.

Будем использовать самоподписанные сертификаты, поскольку VPN-сервером планируем пользоваться только мы. Для того 
чтобы создать сертификаты, потребуется пакет strongswan-pki. Установим его:

`apt-get install strongswan-pki`

### 2. Установка vpn_ike2

Скачиваем скрипты этого проекта, например, в домашнюю директорию.

```
git clone --depth 1 https://github.com/chemandante/vpn_ikev2
cd vpn_ikev2
```

Если скрипты скачали каким-то иным способом, то не забываем дать им разрешение на исполнение:

```
chmod +x *.py
chmod +x *.sh
```

### 3. Создание ключей и сертификатов сервера

В первую очередь нам нужно создать корневой ключ и сертификат, он же “CA” 
(Certificate Authority), который выпустит нам остальные сертификаты. Он будет создан в файлах `ca.pem`: ключ в 
`/etc/ipsec.d/private/`, сертификат в `/etc/ipsec.d/cacerts/`.

Затем создаем ключ и сертификат VPN-сервера, 
требуемый для аутентификации соединения. Назовем его `oscar`, и пусть сервер будет доступен по адресу `oscar.domain.
com`

Оба этих действия создает скрипт:
```
./gen_server_keys.py oscar oscar.domain.com
```
В этом примере созданы корневой сертификат и сертификат сервера `oscar` с доступом по адресу `oscar.domain.com`

Если все прошло нормально, то получим 4 файла:  
`/etc/ipsec.d/cacerts/ca.pem` — сертификат CA (самоподписанный);  
`/etc/ipsec.d/private/ca.pem` — закрытый ключ CA;  
`/etc/ipsec.d/certs/oscar.pem` — сертификат сервера;  
`/etc/ipsec.d/private/oscar.pem` — закрытый ключ сервера.

### 4. Создание ключей и сертификатов клиентов

#### iOS/macOS

Если планируется использование клиентов iOS/macOS, понадобится установка компонента `zsh` на сервере:

```
apt-get install zsh
```
Процесс создания сертификата тут: [Настройка клиента iOS/macOS](ios.html)

#### Windows

Если планируется использование клиентов Windows, обратите внимание на [изменения в настройках сервера](#для-клиентов-windows).

Процесс создания сертификата тут: [Настройка клиента Windows](win.html)

### 5. Настройка strongSwan

Очистим дефолтный конфиг strongSwan командой

```
> /etc/ipsec.conf
```

Создадим свой в текстовом редакторе nano:

```
nano /etc/ipsec.conf
```
Вставляем в него следующий текст, заменив YOUR_VPN_IP на внешний IP-адрес (или FQDN) сервера, а YOUR_VPN_CERT на имя 
файла с сертификатом сервера (в нашем примере `oscar.domain.com` и `oscar.pem`, соответственно):

```
config setup
        uniqueids=keep
        charondebug="ike 2, knl 2, cfg 2, net 2, esp 2, dmn 2,  mgr 2"

conn %default
        keyexchange=ikev2
        ike=aes128gcm16-sha2_256-prfsha256-ecp256!
        esp=aes128gcm16-sha2_256-ecp256!
        fragmentation=yes
        rekey=no
        compress=yes
        dpdaction=clear
        left=%any
        leftauth=pubkey
        leftsourceip=YOUR_VPN_IP
        leftid=YOUR_VPN_IP
        leftcert=YOUR_VPN_CERT
        leftsendcert=always
        leftsubnet=0.0.0.0/0
        right=%any
        rightauth=pubkey
        rightsourceip=10.10.10.0/24
        rightdns=8.8.8.8,8.8.4.4

conn ikev2-pubkey
        auto=add
``` 
       
Внимание! strongSwan требователен к отступам в конфиге, поэтому удостоверьтесь, что параметры каждого раздела конфига отбиты через Tab, как это показано на примере, или хотя бы через один пробел, иначе strongSwan не запустится.

Добавим в файл `ipsec.secrets`, который является хранилищем ссылок на сертификаты и ключи аутентификации, указатель 
на наш сертификат сервера (дан пример с файлом `oscar.pem`):

```
nano /etc/ipsec.secrets
```

```
: RSA oscar.pem
```
Пробелы исключительно важны! Двоеточие, пробел, "RSA", пробел, имя файла — только так и не иначе.

На этом настройка strongSwan завершена, можно перезапустить службу:

```
ipsec restart
```

Если всё хорошо, то сервер запустится:

```
Starting strongSwan 5.9.1 IPsec [starter]...
```

Если упадет в ошибку, то можно посмотреть, что именно произошло, почитав системный лог. Команда выведет 50 последних строк лога:
```
tail -n 50 > /var/log/syslog
```

### 6. Настройка сетевых параметров ядра

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

### 7. Настройка iptables

iptables — это утилита, которая управляет встроенным в Linux файрволом netfilter. Для того чтобы сохранять правила iptables в файле и подгружать их при каждом запуске системы, установим пакет iptables-persistent:

```
apt-get install iptables-persistent
```

После установки нас спросят, сохранить ли текущие правила IPv4 и IPv6. Ответим «Нет», так как у нас новая система, и по сути нечего сохранять.

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

### 8. Проверка

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

### 9. Уборка

Во-первых, закрытые ключи клиентов на сервере не нужны - после создания профилей клиентских устройств (iOS/mscOS) 
или сертификатов (Windows) эти ключи надо удалить. Они находятся в папке `/etc/ipsec.d/private`. По-умолчанию, 
скрипт генерации клиентских сертификатов `gen_client_key.py` удаляет эти ключи автоматически.

Во-вторых, если не планируется больше выпускать клиентские сертификаты, то можно удалить и закрытый корневой ключ 
удостоверяющего центра (CA) (`/etc/ipsec.d/private/ca.pem`).

**Важно!** Не удалите закрытый ключ сервера из этой же папки (в нашем примере `oscar.pem`) — он необходим!

### 10. Разные тонкости

#### Подсоединение нескольких клиентов по одному сертификату

Если есть желание разрешить подсоединение нескольких клиентов по одному сертификату (ну, мало ли), то в файле 
`/etc/ipsec.conf` строку `uniqueids=keep` надо заменить на `uniqueids=never`

#### Для клиентов Windows

Если планируется использование клиентов Windows, то в файл `/etc/ipsec.conf` необходимо внести следующие изменения:

Строки

```
    ike=aes128gcm16-sha2_256-prfsha256-ecp256!
    esp=aes128gcm16-sha2_256-ecp256!
```
заменить на
```
    ike=aes128gcm16-sha2_256-prfsha256-ecp256-modp2048-modp1024
    esp=aes128gcm16-sha2_256-ecp256
```
Эта замена связана с невозможностью Windows поддержать по-умолчанию те криптоалгоритмы, кторые требует сервер. 
Фактически, это ослабляет криптографию, но не критично.

_Где-то я находил иное, более изящное решение проблемы. При 
первой возможности, опишу его здесь_.