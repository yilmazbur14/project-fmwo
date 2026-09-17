Add-Type -AssemblyName System.Drawing
$pfc = New-Object System.Drawing.Text.PrivateFontCollection
$pfc.AddFontFile("C:\Users\theyi\OneDrive\Documents\new-game-project\fonts\PixelifySans.ttf")
$fam = $pfc.Families[0]
Write-Output ("family: " + $fam.Name)
$bmp = New-Object System.Drawing.Bitmap(10,10)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
$fmt = [System.Drawing.StringFormat]::GenericTypographic
foreach ($t in @(@(99,"Defeat!"), @(55,"RETURN TO MAIN MENU"), @(33,"RETURN TO MAIN MENU"), @(33,"@newcomer was kicked from #arena-1."), @(33, "Invite revoked. Train up and try again."), @(33,"SYSTEM"))) {
  $f = New-Object System.Drawing.Font($fam, [single]$t[0], [System.Drawing.FontStyle]::Regular, [System.Drawing.GraphicsUnit]::Pixel)
  $s = $g.MeasureString($t[1], $f, 5000, $fmt)
  Write-Output ("{0} px '{1}': {2} x {3}; ascent={4} lineh={5}" -f $t[0], $t[1], [int]$s.Width, [int]$s.Height, $fam.GetCellAscent(0), $fam.GetLineSpacing(0))
}
Write-Output ("em=" + $fam.GetEmHeight(0))
