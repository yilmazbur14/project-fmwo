param(
  [string]$Bg, [string]$Logo, [string]$Out,
  [int]$LogoX = 72, [int]$LogoY = 84,
  [int]$BtnX = 156, [int]$BtnY = 420, [int]$BtnW = 480, [int]$BtnH = 126,
  [int]$VolY = 600, [int]$SliderX = 156, [int]$SliderY = 660, [int]$SliderW = 480,
  [double]$Value = 0.7, [string]$Overlay = '', [string]$SliderTex = ''
)
Add-Type -AssemblyName System.Drawing
$proj = "C:\Users\theyi\OneDrive\Documents\new-game-project"
$pfc = New-Object System.Drawing.Text.PrivateFontCollection
$pfc.AddFontFile("$proj\fonts\PixelifySans.ttf")
$fam = $pfc.Families[0]

$W = 1920; $H = 1080
$bmp = New-Object System.Drawing.Bitmap($W, $H, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::NearestNeighbor
$g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::Half
$g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::None

function DrawScaled($path, $x, $y, $s) {
  $img = New-Object System.Drawing.Bitmap($path)
  $g.DrawImage($img, (New-Object System.Drawing.Rectangle($x, $y, ($img.Width * $s), ($img.Height * $s))), 0, 0, $img.Width, $img.Height, [System.Drawing.GraphicsUnit]::Pixel)
  $img.Dispose()
}

function NineSlice($path, $x, $y, $w, $h, $m) {
  $img = New-Object System.Drawing.Bitmap($path)
  $tw = $img.Width; $th = $img.Height
  $sx = @(0, $m, ($tw - $m), $tw); $dx = @($x, ($x + $m), ($x + $w - $m), ($x + $w))
  $sy = @(0, $m, ($th - $m), $th); $dy = @($y, ($y + $m), ($y + $h - $m), ($y + $h))
  for ($i = 0; $i -lt 3; $i++) { for ($j = 0; $j -lt 3; $j++) {
    $dst = New-Object System.Drawing.Rectangle($dx[$i], $dy[$j], ($dx[$i+1] - $dx[$i]), ($dy[$j+1] - $dy[$j]))
    $g.DrawImage($img, $dst, $sx[$i], $sy[$j], ($sx[$i+1] - $sx[$i]), ($sy[$j+1] - $sy[$j]), [System.Drawing.GraphicsUnit]::Pixel)
  }}
  $img.Dispose()
}

function NineSlice4($path, $x, $y, $w, $h, $ml, $mt, $mr, $mb) {
  $img = New-Object System.Drawing.Bitmap($path)
  $tw = $img.Width; $th = $img.Height
  $sx = @(0, $ml, ($tw - $mr), $tw); $dx = @($x, ($x + $ml), ($x + $w - $mr), ($x + $w))
  $sy = @(0, $mt, ($th - $mb), $th); $dy = @($y, ($y + $mt), ($y + $h - $mb), ($y + $h))
  for ($i = 0; $i -lt 3; $i++) { for ($j = 0; $j -lt 3; $j++) {
    $dw = $dx[$i+1] - $dx[$i]; $dh = $dy[$j+1] - $dy[$j]
    if ($dw -le 0 -or $dh -le 0) { continue }
    $dst = New-Object System.Drawing.Rectangle($dx[$i], $dy[$j], $dw, $dh)
    $g.DrawImage($img, $dst, $sx[$i], $sy[$j], ($sx[$i+1] - $sx[$i]), ($sy[$j+1] - $sy[$j]), [System.Drawing.GraphicsUnit]::Pixel)
  }}
  $img.Dispose()
}

function Rect($x, $y, $w, $h, $hex) {
  $c = [System.Drawing.ColorTranslator]::FromHtml("#$hex")
  $b = New-Object System.Drawing.SolidBrush($c)
  $g.FillRectangle($b, $x, $y, $w, $h)
  $b.Dispose()
}

function Text($txt, $size, $cx, $cy, $hex, $shadowHex) {
  $g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::SingleBitPerPixelGridFit
  $f = New-Object System.Drawing.Font($fam, $size, [System.Drawing.FontStyle]::Regular, [System.Drawing.GraphicsUnit]::Pixel)
  $sz = $g.MeasureString($txt, $f)
  $x = [int]($cx - $sz.Width / 2); $y = [int]($cy - $sz.Height / 2)
  if ($shadowHex -ne '') {
    $sb = New-Object System.Drawing.SolidBrush([System.Drawing.ColorTranslator]::FromHtml("#$shadowHex"))
    $g.DrawString($txt, $f, $sb, ($x + 3), ($y + 3)); $sb.Dispose()
  }
  $br = New-Object System.Drawing.SolidBrush([System.Drawing.ColorTranslator]::FromHtml("#$hex"))
  $g.DrawString($txt, $f, $br, $x, $y)
  $br.Dispose(); $f.Dispose()
}

DrawScaled $Bg 0 0 3
if ($Overlay -ne '') { DrawScaled $Overlay 0 0 3 }
DrawScaled $Logo $LogoX $LogoY 3

# NEW GAME button (ui_button_3x 9-slice, 24px margins, same as the controls screen)
NineSlice "$proj\Assets\UI\ui_button_3x.png" $BtnX $BtnY $BtnW $BtnH 24
Text "NEW GAME" 55 ($BtnX + $BtnW / 2) ($BtnY + $BtnH / 2 + 1) "ffffff" ""

# VOLUME label + slider (track built from the kit palette, 3px grid)
Text "VOLUME" 33 ($SliderX + $SliderW / 2) $VolY "ffffff" "000000"
$tx = $SliderX; $ty = $SliderY; $tw = $SliderW; $th = 30
if ($SliderTex -ne '') {
  # exactly what Godot's HSlider draws: track stylebox over the rect, fill stylebox from the left edge to the
  # grabber centre (areasize * ratio + grabber_w / 2), grabber icon at ratio * (width - grabber_w), all
  # vertically centred on the control (control = 480x54 at y 648, so the 30px track sits at 660..690)
  $area = $tw - 36
  NineSlice4 "$SliderTex\menu_slider_track_3x.png" $tx $ty $tw $th 9 12 9 9
  $fw = [int][math]::Floor($area * $Value + 18)
  NineSlice4 "$SliderTex\menu_slider_fill_3x.png" $tx $ty $fw $th 9 12 9 9
  DrawScaled "$SliderTex\menu_slider_grabber_3x.png" ($tx + [int][math]::Floor($area * $Value)) ($ty + 15 - 27) 1
} else {
Rect $tx $ty $tw $th "000000"
Rect ($tx + 3) ($ty + 3) ($tw - 6) ($th - 6) "8a6f30"
Rect ($tx + 3) ($ty + 3) ($tw - 6) 3 "d9a066"
Rect ($tx + 6) ($ty + 6) ($tw - 12) ($th - 12) "000000"
Rect ($tx + 9) ($ty + 9) ($tw - 18) ($th - 18) "222034"
$fillW = [int](($tw - 18) * $Value / 3) * 3
Rect ($tx + 9) ($ty + 9) $fillW ($th - 18) "ac3232"
Rect ($tx + 9) ($ty + 9) $fillW 3 "d95763"
$kx = $tx + 9 + $fillW - 18; $ky = $ty - 12
Rect $kx $ky 36 54 "000000"
Rect ($kx + 3) ($ky + 3) 30 48 "8a6f30"
Rect ($kx + 3) ($ky + 3) 27 45 "d9a066"
Rect ($kx + 3) ($ky + 3) 24 6 "fbf236"
Rect ($kx + 12) ($ky + 18) 12 18 "8a6f30"
}

$g.Dispose()
$bmp.Save($Out, [System.Drawing.Imaging.ImageFormat]::Png)
$bmp.Dispose()
Write-Output "mockup -> $Out"
