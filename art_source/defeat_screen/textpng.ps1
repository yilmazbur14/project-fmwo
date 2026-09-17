param([string]$OutDir, [string]$Spec)
# Renders each text item to its own transparent PNG (aliased, like Godot with antialiasing off).
# Spec: "name|size|text;;name|size|text"
Add-Type -AssemblyName System.Drawing
$pfc = New-Object System.Drawing.Text.PrivateFontCollection
$pfc.AddFontFile("C:\Users\theyi\OneDrive\Documents\new-game-project\fonts\PixelifySans.ttf")
$fam = $pfc.Families[0]
$fmt = [System.Drawing.StringFormat]::GenericTypographic
foreach ($item in ($Spec -split ';;')) {
  if ($item.Trim() -eq '') { continue }
  $p = $item -split '\|', 3
  $name = $p[0]; $sz = [int]$p[1]; $txt = $p[2]
  $f = New-Object System.Drawing.Font($fam, [single]$sz, [System.Drawing.FontStyle]::Regular, [System.Drawing.GraphicsUnit]::Pixel)
  $tmp = New-Object System.Drawing.Bitmap(4, 4)
  $g0 = [System.Drawing.Graphics]::FromImage($tmp)
  $s = $g0.MeasureString($txt, $f, 10000, $fmt)
  $g0.Dispose(); $tmp.Dispose()
  $lineh = [int][Math]::Ceiling($sz * 1.2)
  $w = [int][Math]::Ceiling($s.Width) + 4
  $bmp = New-Object System.Drawing.Bitmap($w, $lineh, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
  $g = [System.Drawing.Graphics]::FromImage($bmp)
  $g.Clear([System.Drawing.Color]::FromArgb(0,0,0,0))
  $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::None
  $path = New-Object System.Drawing.Drawing2D.GraphicsPath([System.Drawing.Drawing2D.FillMode]::Winding)
  $path.AddString($txt, $fam, 0, [single]$sz, (New-Object System.Drawing.PointF(0, 0)), $fmt)
  $path.FillMode = [System.Drawing.Drawing2D.FillMode]::Winding
  $g.FillPath([System.Drawing.Brushes]::White, $path)
  $path.Dispose()
  $g.Dispose()
  $bmp.Save((Join-Path $OutDir ($name + ".png")), [System.Drawing.Imaging.ImageFormat]::Png)
  $bmp.Dispose(); $f.Dispose()
  Write-Output ("{0} {1}x{2} measured {3}" -f $name, $w, $lineh, [int]$s.Width)
}
