Установка strongSwan

Установим strongSwan:

apt-get install strongswan
К детальной настройке strongSwan мы вернемся чуть позже, а пока создадим сертификаты, чтобы наши устройства смогли подключиться по VPN.

Генерируем сертификаты доступа

Мы будем использовать самозаверенные сертификаты, поскольку VPN-сервером планируем пользоваться только мы. Для того чтобы создать сертификаты, нам потребуется пакет strongswan-pki. Установим его:

apt-get install strongswan-pki
Переходим к созданию сертификатов. В первую очередь нам нужно создать корневой сертификат, он же “CA” (Certificate Authority), который выпустит нам остальные сертификаты. Создадим его в файле ca.pem:

cd /etc/ipsec.d
ipsec pki --gen --type rsa --size 4096 --outform pem > private/ca.pem
ipsec pki --self --ca --lifetime 3650 --in private/ca.pem \
> --type rsa --digest sha256 \
> --dn "CN=YOUR_LIGHTSAIL_IP" \
> --outform pem > cacerts/ca.pem
Далее создадим сертификат для нашего VPN-сервера в файле debian.pem:

ipsec pki --gen --type rsa --size 4096 --outform pem > private/debian.pem
ipsec pki --pub --in private/debian.pem --type rsa |
> ipsec pki --issue --lifetime 3650 --digest sha256 \
> --cacert cacerts/ca.pem --cakey private/ca.pem \
> --dn "CN=YOUR_LIGHTSAIL_IP" \
> --san YOUR_LIGHTSAIL_IP \
> --flag serverAuth --outform pem > certs/debian.pem
А теперь создадим сертификат для наших устройств в файле me.pem:

ipsec pki --gen --type rsa --size 4096 --outform pem > private/me.pem
ipsec pki --pub --in private/me.pem --type rsa |
> ipsec pki --issue --lifetime 3650 --digest sha256 \
> --cacert cacerts/ca.pem --cakey private/ca.pem \
> --dn "CN=me" --san me \
> --flag clientAuth \
> --outform pem > certs/me.pem
Для надежности удалим файл ca.pem, он нам больше не потребуется:

rm /etc/ipsec.d/private/ca.pem
Создание сертификатов завершено.


Настроим сам strongSwan

Очистим дефолтный конфиг strongSwan командой:

> /etc/ipsec.conf
И создадим свой в текстовом редакторе nano:

nano /etc/ipsec.conf
Вставьте данный текст в него, заменив YOUR_LIGHTSAIL_IP на внешний IP-адрес машины в AWS Lightsail:

include /var/lib/strongswan/ipsec.conf.inc

config setup
        uniqueids=never
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
        leftsourceip=YOUR_LIGHTSAIL_IP
        leftid=YOUR_LIGHTSAIL_IP
        leftcert=debian.pem
        leftsendcert=always
        leftsubnet=0.0.0.0/0
        right=%any
        rightauth=pubkey
        rightsourceip=10.10.10.0/24
        rightdns=8.8.8.8,8.8.4.4

conn ikev2-pubkey
        auto=add
Внимание! strongSwan требователен к отступам в конфиге, поэтому удостоверьтесь, что параметры каждого раздела конфига отбиты через Tab, как это показано на примере, или хотя бы через один пробел, иначе strongSwan не запустится.

Сохраним файл с помощью Ctrl+X и пойдем дальше.

Добавим в файл ipsec.secrets, который является хранилищем ссылок на сертификаты и ключи аутентификации, указатель на наш сертификат сервера:

nano /etc/ipsec.secrets
include /var/lib/strongswan/ipsec.secrets.inc

: RSA debian.pem
На этом настройка Strongswan завершена, можно рестартнуть службу:

ipsec restart
Если всё хорошо, то сервер запустится:

...
Starting strongSwan 5.5.1 IPsec [starter]...
Если упадет в ошибку, то можно посмотреть, что именно произошло, почитав системный лог. Команда выведет 50 последних строк лога:

tail -n 50 > /var/log/syslog
Настроим сетевые параметры ядра

Теперь нам необходимо внести некоторые изменения в файл /etc/sysctl.conf.

nano /etc/sysctl.conf
Через Ctrl+W найдем в файле следующие переменные и внесем в них изменения:

#Раскомментируем данный параметр, чтобы включить переадресацию пакетов
net.ipv4.ip_forward = 1

#Раскомментируем данный параметр, чтобы предотвратить MITM-атаки
net.ipv4.conf.all.accept_redirects = 0

#Раскомментируем данный параметр, чтобы запретить отправку ICMP-редиректов
net.ipv4.conf.all.send_redirects = 0

...

#В любом месте файла на новой строке добавим данный параметр, запретив поиск PMTU
net.ipv4.ip_no_pmtu_disc = 1
Подгрузим новые значения:

sysctl -p
Настройка сетевых параметров ядра завершена.



Настроим iptables

iptables — это утилита, которая управляет встроенным в Linux файрволом netfilter. Для того, чтобы сохранять правила iptables в файле и подгружать их при каждом запуске системы, установим пакет iptables-persistent:

apt-get install iptables-persistent
После установки нас спросят, сохранить ли текущие правила IPv4 и IPv6. Ответим «Нет», так как у нас новая система, и по сути нечего сохранять.

Перейдем к формированию правил iptables. На всякий пожарный, очистим все цепочки:

iptables -P INPUT ACCEPT
iptables -P FORWARD ACCEPT
iptables -F
iptables -Z
Разрешим соединения по SSH на 22 порту, чтобы не потерять доступ к машине:

iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
iptables -A INPUT -p tcp --dport 22 -j ACCEPT
Разрешим соединения на loopback-интерфейсе:

iptables -A INPUT -i lo -j ACCEPT
Теперь разрешим входящие IPSec-соединения на UDP-портах 500 и 4500:

iptables -A INPUT -p udp --dport  500 -j ACCEPT
iptables -A INPUT -p udp --dport 4500 -j ACCEPT
Разрешим переадресацию ESP-трафика:

iptables -A FORWARD --match policy --pol ipsec --dir in  --proto esp -s 10.10.10.0/24 -j ACCEPT
iptables -A FORWARD --match policy --pol ipsec --dir out --proto esp -d 10.10.10.0/24 -j ACCEPT
Настроим маскирование трафика, так как наш VPN-сервер, по сути, выступает как шлюз между Интернетом и VPN-клиентами:

iptables -t nat -A POSTROUTING -s 10.10.10.0/24 -o eth0 -m policy --pol ipsec --dir out -j ACCEPT
iptables -t nat -A POSTROUTING -s 10.10.10.0/24 -o eth0 -j MASQUERADE
Настроим максимальный размер сегмента пакетов:

iptables -t mangle -A FORWARD --match policy --pol ipsec --dir in -s 10.10.10.0/24 -o eth0 -p tcp -m tcp --tcp-flags SYN,RST SYN -m tcpmss --mss 1361:1536 -j TCPMSS --set-mss 1360
Запретим все прочие соединения к серверу:

iptables -A INPUT -j DROP
iptables -A FORWARD -j DROP
Сохраним правила, чтобы они загружались после каждой перезагрузки:

netfilter-persistent save
netfilter-persistent reload
Настройка iptables завершена.


Перезагрузим машину:

reboot
И посмотрим работают ли правила iptables:

sudo su
iptables -S
root@XX.XX.XX.XX:/home/admin# iptables -S
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
Да, всё работает.

Работает ли strongSwan:

ipsec statusall
root@XX.XX.XX.XX:/home/admin# ipsec statusall
Status of IKE charon daemon (strongSwan 5.5.1, Linux 4.9.0-8-amd64, x86_64):
  uptime: 71 seconds, since Jan 23 23:22:16 2019

...
Да, всё работает.


Создаем .mobileconfig для iPhone, iPad и Mac

Мы будем использовать один VPN-профайл .mobileconfig для всех наших устройств: iPhone, iPad и Mac. Конфиг, который мы сделаем, устроен таким образом, чтобы инициировать соединение “On Demand”. Это означает, что при попытке любой службы или приложения выйти в Интернет, VPN-соединение будет всегда устанавливаться принудительно и автоматически. Таким образом, удастся избежать ситуации, когда вы забыли установить VPN-соединение, например, после перезагрузки устройства, а трафик в итоге пошел через провайдера, что нам совсем не нужно.

Скачаем скрипт, который сгенерирует для нас данный конфиг:

wget https://gist.githubusercontent.com/borisovonline/955b7c583c049464c878bbe43329a521/raw/966e8a1b0a413f794280aba147b7cea0661f77a8/mobileconfig.sh
Для того, чтобы скрипт отработал, нам потребуется пакет zsh, установим его:

apt-get install zsh
Отредактируем название сервера по вкусу, а также пропишем внешний IP-адрес машины Lightsail, который мы указывали при создании сертификатов:

nano mobileconfig.sh
...

SERVER="AWS Frankfurt"
FQDN="YOUR_LIGHTSAIL_IP"

...
Запустим скрипт и на выходе получим готовый файл iphone.mobileconfig:

chmod u+x mobileconfig.sh
./mobileconfig.sh > iphone.mobileconfig
Заберите этот файл с сервера, подключившись с помощью любого SFTP-клиента, например, Transmit или Cyberduck, и отправьте его на все ваши устройства через Airdrop. Подтвердите на устройствах установку конфигурации.

