# ChemStation Skriptování a Makra – Praktický Tutoriál (Rozšířená verze)

Tento dokument shrnuje praktické základy skriptování v Agilent ChemStation a doplňuje detailní popis práce s registry a RC.NET moduly.

---

## 1. Příkazy v ChemStation

ChemStation obsahuje příkazový procesor (CP), který interpretuje a vykonává příkazy.

- **Zobrazení zprávy:**
  ```
  Print "Toto je zpráva"
  ```
- **Více příkazů na řádku:** oddělujeme `;`.
  ```
  Print "Startuji"; Sleep 2; Print "Hotovo"
  ```
- **Komentáře:** Text za `!` je ignorován.
  ```
  ! Toto je komentář
  ```
- **Historie:** Pomocí kláves `↑` a `↓` lze vybírat předchozí příkazy.

---

## 2. Makra – Struktura a Parametry

Makro je sada příkazů pod společným názvem. Slouží k automatizaci úloh.

### Základní struktura
```
Name MyMessage
    Print "Hello World!"
EndMacro
```

### Komentáře
V makrech se komentáře označují `!`.

### Parametry makra
Makra mohou mít jeden nebo více parametrů deklarovaných pomocí `Parameter`:
```
Name InjectSample
    Parameter SampleName$, VialPos, InjVol
    Print "Sample=", SampleName$, ", Vial=", VialPos, ", InjVol=", InjVol
EndMacro
```
Volání:
```
InjectSample "Std_1", 5, 10
```

### Lokální proměnné
Proměnné uvnitř makra se definují příkazem `Local`.
```
Name Calculate
    Local Area, Volume
    Area = 2.5
    Volume = Area * 10
    Print "Volume =", Volume
EndMacro
```

---

## 3. Ukládání a Zavádění Maker

- **Načtení makra:**
  ```
  Macro "mymacro.mac"
  ```
- **Načtení makra s absolutní cestou:**
  ```
  Macro "D:\projekty\chem\mymacro.mac"
  ```
- **Spuštění makra:**
  ```
  MyMessage "Vzorek A"
  ```
- **Odstranění makra:**
  ```
  Remove MyMessage
  ```

---

## 4. Proměnné

- **String:** `Sample$ = "Test"`
- **Numerické:** `Flow = 1.5`
- **Systémové proměnné:** `_DataFile$`, `_MethodOn`, `_SequenceOn`, `_AutoPath$`

Pro kompletní seznam zadej:
```
Show
```

---

## 5. Registry

Registry uchovávají komplexní data o analýzách, metodách, chromatogramech nebo spektrech.

### Základní práce s registry
```
Print RegSize(ChromReg)
Print RegCont$(ChromReg)
ChromReg[1]
```

### Čtení dat
```
Data(ChromReg[1], 0, 10)  ! 10. bod X-osa
Data(ChromReg[1], 1, 10)  ! 10. bod Y-osa
```

### Čtení tabulek
```
TabText$(ChromRes[1], "Peak", 2, "Name")
TabVal(ChromRes[1], "Peak", 2, "Area")
```

### Úprava registrů
Data lze upravit příkazy `SetData`, `SetObjHdrVal` apod. Například:
```
SetObjHdrVal ChromReg[1], "Title", "Můj chromatogram"
```

### Úrovně registrů
- **Registr** – obsahuje objekty (např. chromatogramy).
- **Objekt** – obsahuje hlavičku (metadata) a datové bloky.
- **Tabulky** – detailní výsledky (píky, kvantifikace).

> Pro procházení všech registrů použij `register_reader.mac`.

---

## 6. RC.NET Ovladače

### RC.NET registry
Každý modul má tři základní registry:
- `RC<ModID><#>Method` – parametry metody.
- `RC<ModID><#>Status` – aktuální stav (tlaky, teploty).
- `RC<ModID><#>Config` – informace o modulu (typ, verze firmware).

### Úprava parametrů metody
```
UploadRCMethod PMP1
SetObjHdrVal RCPMP1Method[1], "StopTime_Time", 10
DownloadRCMethod PMP1
```

### Zjišťování informací o modulu
```
Print ObjHdrVal(RCPMP1Status[1], "Pressure")
Print ObjHdrVal(RCPMP1Config[1], "SerialNumber")
```

### Posílání příkazů
- **WriteModule** – čistě odešle příkaz bez čtení odpovědi.
  ```
  WriteModule "WLS1","LRPL 10"
  ```
- **SendModule$** – odešle příkaz a vrátí odpověď.
  ```
  Print SendModule$("WLS1","LIFTER:OCCUPIED? 3")
  ```

### Jak zjistit příkazy

Specifické příkazy pro jednotlivé moduly lze zjistit čtením logu `rcdriver.trc`. Postup:
1. Otevři adresář `C:\Chem32\1\TEMP` (nebo aktuální temp složku ChemStation).
2. Spusť požadovanou akci v uživatelském rozhraní (např. start purge).
3. Otevři soubor `rcdriver.trc` v textovém editoru (Notepad++).
4. Hledej řádky začínající `Instruction:` – obsahují přesné příkazy, které lze poslat přes `SendModule$` nebo `WriteModule`.
5. Zjištěný příkaz vyzkoušej v CP, např.:
   ```
   Print SendModule$("PMP1","<příkaz>")
   ```

---

## 7. Tipy a Doporučení

- Makra lze spouštět při startu pomocí `user.mac`.
- Používej `register_reader.mac` pro detailní průzkum registrů.
- RC.NET moduly vypíšeš pomocí `RCListDevices$()`.

