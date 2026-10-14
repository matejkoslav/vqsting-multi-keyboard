# Prostredie a prístup

Kontext pre AI asistenta, aby nabudúce hneď vedel, kde sme a čo je dostupné.

## Host
- Omarchy (Arch + Hyprland). Projekt **nie je git repo**.
- Cesta: `~/Documents/School_not_synched/skupinovy_projekt/`
- KVM funguje: `/dev/kvm` existuje, CPU má `vmx|svm`.
- Nainštalované: `docker`, `docker-buildx`, `docker-compose`, `lazydocker`, `qemu-user-static`.
  **Chýba:** `libvirt`, `virt-manager` (libvirtd inactive).
- **Prístup AI:** k súborom áno (read/edit priamo). Do Windows VM len GUI/RDP (viď nižšie).

## Windows VM — `omarchy-windows-vm` (odporúčané)
Vstavané v Omarchy: menu **Windows → Install**, binárka `omarchy-windows-vm`.
- Windows 11 ako **Docker kontajner + KVM** (dockur/windows image), `/dev/kvm` vnútri.
- Ovládanie: **RDP** cez `xfreerdp3` na `127.0.0.1:3389`; priebeh inštalácie na `http://127.0.0.1:8006`.
- Príkazy: `omarchy windows vm install|launch|stop|status|remove` (`launch -k` = nechať bežať po RDP).
- Dáta: `~/.windows` (disk) + `~/Windows` (zdieľaný priečinok do guesta).
- Predpoklady: bežiaci Docker daemon, ~42 GB voľného miesta (32G disk + 10G ISO), odporúčané 64G.
- **Prístup AI do guesta:** default len RDP (GUI). SSH by šlo len ak v Windows zapneš OpenSSH a namapuješ
  port — kontajner mapuje len `8006` a `3389`. MPV fullscreen cez RDP funguje (`/gfx:AVC444`).

## Manuálny QEMU/KVM (alternatíva, netreba)
`qemu-full virt-manager libvirt edk2-ovmf swtpm` + `systemctl enable --now libvirtd` + user do `libvirt`
grupy. Omarchy-windows-vm toto obchádza.

## Kľúčová vec: prečo VM/Docker neotestuje našu funkciu
Cieľ = rozlíšiť **N klávesníc** podľa USB portu cez Windows Raw Input:
- `RegisterRawInputDevices` (usage page 1, usage 6, `RIDEV_INPUTSINK`, skryté okno),
- `WM_INPUT` → `GetRawInputData` → `hDevice`,
- `GetRawInputDeviceInfo(RIDI_DEVICENAME)` → `\\?\HID#VID_...&0&0000#{...}`; `7&2f...&0&0000` = USB port.
- Musí to byť **natívny Python proces** (browser nevie per-device vstup). `pynput`/`keyboard` nepoužiteľné
  (nerozlíšia zariadenie). `pip install rawinput` alebo ctypes/pywin32.
- **RDP posiela vstup ako jednu syntetickú klávesnicu** → guest nevidí per-port HID → test v VM je bezcenný.
  Nutný reálny Windows HW (Patrik).

## Dve architektúry
- **A) Group mód** (1 PC, 1 obrazovka, N klávesníc): všetci pozerajú to isté video (1 MPV, 1 zvuk); po skončení
  N panelov, každý stlačí 1–5 na svojej klávesnici. Treba natívny listener (`keyboard_listener.py`) → Flask
  endpoint → zápis do `Valuation` s identitou slotu.
- **B) Multi-seat** (ASTER / Windows MultiPoint): 1 PC = N nezávislých pracovísk. Appka beží N inštancií
  (rôzne porty) → každý tester je normálny user. Jednoduchšie, bez Raw Input. Ak nemusia vidieť to isté video.

## Ďalšie kroky
1. Overiť appku na Windows (Patrik): `VQSTing.bat`, admin/admin, test, export CSV.
2. So zadávateľom vyjasniť: A alebo B? spoločné video? koľko testerov, koľko monitorov?
3. Prototyp: `keyboard_listener.py` vytlačí `RIDI_DEVICENAME` pri stlačení na každej z 2 klávesníc → 2 rôzne ID.
4. Až potom implementácia + test s 2 klávesnicami.
