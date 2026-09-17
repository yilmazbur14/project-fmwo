param([string]$In, [string]$Out, [int]$Scale = 8, [string]$Bg = 'checker')
Add-Type -AssemblyName System.Drawing
$src = New-Object System.Drawing.Bitmap($In)
$w = $src.Width * $Scale; $h = $src.Height * $Scale
$dst = New-Object System.Drawing.Bitmap($w, $h, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
$g = [System.Drawing.Graphics]::FromImage($dst)
if ($Bg -eq 'checker') {
  $c1 = [System.Drawing.Color]::FromArgb(255,210,210,210)
  $c2 = [System.Drawing.Color]::FromArgb(255,170,170,170)
  $b1 = New-Object System.Drawing.SolidBrush($c1)
  $b2 = New-Object System.Drawing.SolidBrush($c2)
  $cell = $Scale * 4
  for ($y=0; $y -lt $h; $y+=$cell) { for ($x=0; $x -lt $w; $x+=$cell) {
    $br = if ((($x/$cell) + ($y/$cell)) % 2 -eq 0) { $b1 } else { $b2 }
    $g.FillRectangle($br, $x, $y, $cell, $cell)
  }}
} else {
  $g.Clear([System.Drawing.Color]::White)
}
$g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::NearestNeighbor
$g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::Half
$g.DrawImage($src, 0, 0, $w, $h)
$g.Dispose()
$dst.Save($Out, [System.Drawing.Imaging.ImageFormat]::Png)
$dst.Dispose(); $src.Dispose()
Write-Output "OK -> $Out ($w x $h)"
