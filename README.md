git checkout docs/readme-and-contributing
$rows = @"
| Ferdnard Bosire | ferddy999 | Team leader; front end and database |
| Esther Atuti | esther385 | Assistant team leader; coordination and code review |
| Felix Nyandiko | silentecho2 | Back end: staff and office records |
| George Gisemba | prof279 | Sign-in, one-time codes and security |
| Juliet Juma | julietjuma70-tech | Testing and quality assurance |
| Zachary Monayo | zacharymonayo | Validation and audit trail |
| Andy Joshua | andy9128 | Documentation and deployment guide |
| Diana Muthuri | diane200-igtm | Wireframes and phone layout |
"@
$t = Get-Content README.md -Raw
$t = [regex]::Replace($t, "(\|\s*\|\s*\|\s*\|\r?\n){3}", ($rows -replace "\r?\n", "`n") + "`n")
[System.IO.File]::WriteAllText("$PWD\README.md", $t, (New-Object System.Text.UTF8Encoding($false)))
Select-String -Path README.md -Pattern "ferddy999"