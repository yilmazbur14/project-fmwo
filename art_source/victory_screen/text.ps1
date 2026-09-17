param([string]$In, [string]$Out, [string]$SpecFile)
# Draws Pixelify Sans text onto a PNG. Spec file lines: x|y|size|RRGGBB|align|shadowRRGGBB|shadowOffset|text
#   align: L (x = left) or C (x = centre). shadow '-' for none. shadowOffset e.g. 6 (draws an outline ring of that radius)
Add-Type -AssemblyName System.Drawing
$pfc = New-Object System.Drawing.Text.PrivateFontCollection
$pfc.AddFontFile("C:\Users\theyi\OneDrive\Documents\new-game-project\fonts\PixelifySans.ttf")
$fam = $pfc.Families[0]
$src = New-Object System.Drawing.Bitmap($In)
$bmp = New-Object System.Drawing.Bitmap($src.Width, $src.Height, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.DrawImageUnscaled($src, 0, 0)
$src.Dispose()
$g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
$fmt = [System.Drawing.StringFormat]::GenericTypographic
foreach ($line in (Get-Content $SpecFile)) {
  if ($line.Trim() -eq '') { continue }
  $p = $line -split '\|', 8
  $x = [float]$p[0]; $y = [float]$p[1]; $sz = [int]$p[2]; $hex = $p[3]; $al = $p[4]; $sh = $p[5]; $so = [int]$p[6]; $txt = $p[7]
  $f = New-Object System.Drawing.Font($fam, $sz, [System.Drawing.FontStyle]::Regular, [System.Drawing.GraphicsUnit]::Pixel)
  $size = $g.MeasureString($txt, $f, 4000, $fmt)
  if ($al -eq 'C') { $x = $x - $size.Width / 2 }
  if ($sh -ne '-') {
    $sc = [System.Drawing.Color]::FromArgb(255, [Convert]::ToInt32($sh.Substring(0,2),16), [Convert]::ToInt32($sh.Substring(2,2),16), [Convert]::ToInt32($sh.Substring(4,2),16))
    $sb = New-Object System.Drawing.SolidBrush($sc)
    for ($dx = -$so; $dx -le $so; $dx += 3) { for ($dy = -$so; $dy -le $so + 3; $dy += 3) {
      $g.DrawString($txt, $f, $sb, $x + $dx, $y + $dy, $fmt)
    } }
    $sb.Dispose()
  }
  $col = [System.Drawing.Color]::FromArgb(255, [Convert]::ToInt32($hex.Substring(0,2),16), [Convert]::ToInt32($hex.Substring(2,2),16), [Convert]::ToInt32($hex.Substring(4,2),16))
  $br = New-Object System.Drawing.SolidBrush($col)
  $g.DrawString($txt, $f, $br, $x, $y, $fmt)
  Write-Output ("{0}: w={1:N0} h={2:N0} at x={3:N0}" -f $txt, $size.Width, $size.Height, $x)
  $br.Dispose(); $f.Dispose()
}
$g.Dispose()
$bmp.Save($Out, [System.Drawing.Imaging.ImageFormat]::Png)
$bmp.Dispose()
Write-Output "text -> $Out  family=$($fam.Name)"
