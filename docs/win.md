## Настройка клиента Windows

Речь пойдет о настройке Windows 10 для подключения к нашему VPN-серверу на базе strongSwan/IKEv2. Далее в тексте и на скриншотах 
англоязычная версия Windows.

Обратите внимание на [ремарку](server.html#для-клиентов-windows) о настройке сервера для клиентов Windows.

### Создание сертификатов

Сертификаты и ключи клиентского устройства мы будем создавать на нашем сервере вызовом скрипта из данного проекта. 
Следует напомнить, что в примере, описанном в [инструкции по настройке сервера](server.html), сервер был назван 
`oscar` и доступ к нему осуществлялся по `oscar.domain.com`. Назовем клиентское устройство неоригинально, `my_pc`:

```
./gen_client_key.py w my_pc oscar oscar.domain.com
```

В процессе исполнения скрипта надо будет придумать экспортный пароль для шифрования сертификата с ключом. Этот пароль 
потребуется для импорта сертификата в Windows. В итоге будет создан сертификат для устройства `my_pc`.

Если все прошло ок, то добавляются 2 файла:  
`/etc/ipsec.d/certs/my_pc.pem` — сертификат клиентского устройства;  
`my_pc.pfx` — сертификат с ключом для импорта в Windows.

Клич и сертификат готовы.

### Импорт сертификатов 

На каждое клиентское устройство Windows потребуется перенести три файла с сервера для импорта:

`my_pc.pfx` — сертификат с закрытым ключом конкретного клиента для шифрования трафика  
и два файла общих для всех клиентов нашего сервера:  
`/etc/ipsec.d/certs/oscar.pem` — сертификат сервера для аутентификации;  
`/etc/ipsec.d/cacerts/ca.pem` — корневой сертификат CA для удостоверения сертификатов сервера и клиента.

Эти файлы должны быть скачаны на компьютер с Windows.

Открываем консоль MMC:

```
mmc.exe
```

В меню `File → Add/Remove Snap-in...` выбираем `Certificates` и добавляем `Add >`. Появляется диалоговое окно, в 
нем 
поочередно выбираем: `Computer account`, `Local computer`, далее `Finish` и `OK`. Получим окно с деревом сертификатов 
слева.

![img](img/w1.png)

В левой стороне открываем дерево, выбираем папку `Trusted Root Certification Authorities`, в ней `Certificates` и 
жмем на нее правой кнопкой. В контекстном меню `All Tasks → Import...`. В новом диалоговом окне пролистываем до 
момента выбора файла, в котором выбираем наш `ca.pem` (для этого фильтр придется установить в `*.*`). На дальнейший 
вопрос о том, куда поместить файл, отвечаем `Trusted Root Certification Authorities`. Со всем остальным соглашаемся.

![img](img/w2.png)

Аналогичным образом импортируем `oscar.pem`, но в папку `Personal`.

Третий, последний сертификат с закрытым ключем клиента (`my_pc.pfx`) также импортируем в папку `Personal`. В 
процессе импорта понадобится пароль, которым зашифровали сертификат на этапе его выпуска. Все галки оставляем как есть.

![img](img/w3.png)

Обратите внимание на то, что у `my_pc` пиктограмма с ключом. С сертификатами работа завершена, импортированные файлы 
можно удалить.

### Настройка VPN

Идем в настройки Windows, ищем там VPN и добавляем новое VPN-соединение.

![img](img/w4.png)

Заполняем поля как на картинке. Способ аутентификации (на картинке по логину и паролю) оставляем пока как есть.

![img](img/w5.png)

Сохраняем новое соединение и в предыдущем окне переходим к старому традиционному способу настройки сетевых 
интерфейсов по ссылке `Change adapter options`.

![img](img/w6.png)

В списке интерфейсов находим созданный нами (`Oscar VPN`) и заходим в его свойства.

![img](img/w7.png)

В закладке `Security` используем 
сертификаты компьютера `Use machine certificates`.

![img](img/w8.png)

Настройка завершена, можно подключаться.