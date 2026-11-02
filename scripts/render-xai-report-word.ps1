# Render bản báo cáo bằng Microsoft Word trên Windows khi không có LibreOffice.
# Chỉ mở file được chỉ định ở chế độ chỉ đọc, trong một Word instance ẩn riêng.
param(
    [Parameter(Mandatory = $true)][string]$InputDocx,
    [Parameter(Mandatory = $true)][string]$OutputDirectory
)
$ErrorActionPreference = 'Stop'
$inputPath = (Resolve-Path -LiteralPath $InputDocx).Path
$outputPath = [System.IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Path $outputPath -Force | Out-Null
$word = $null
$document = $null
try {
    Write-Output 'Starting isolated Word instance'
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $word.AutomationSecurity = 3
    $confirmConversions = $false
    $readOnly = $true
    $addRecent = $false
    Write-Output 'Opening document read-only'
    $document = $word.Documents.Open([ref]$inputPath, [ref]$confirmConversions, [ref]$readOnly, [ref]$addRecent)
    # Dùng ảnh trang native của Word; tránh phụ thuộc bộ xuất PDF của Office.
    # API: learn.microsoft.com/office/vba/api/word.page.enhmetafilebits
    Add-Type -AssemblyName System.Drawing
    $document.ActiveWindow.View.Type = 3
    $pages = $document.ActiveWindow.Panes.Item(1).Pages
    Write-Output ('Pages=' + $pages.Count)
    for ($pageNumber = 1; $pageNumber -le $pages.Count; $pageNumber++) {
        $page = $pages.Item($pageNumber)
        $bits = [byte[]]$page.EnhMetaFileBits
        $stream = [System.IO.MemoryStream]::new($bits)
        $metafile = [System.Drawing.Imaging.Metafile]::new($stream)
        $width = 1600
        $height = [int][Math]::Round($width * $page.Height / $page.Width)
        $bitmap = [System.Drawing.Bitmap]::new($width, $height)
        $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
        try {
            $graphics.Clear([System.Drawing.Color]::White)
            $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
            $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
            $graphics.DrawImage($metafile, [System.Drawing.Rectangle]::new(0, 0, $width, $height))
            $pngPath = Join-Path $outputPath ('page-' + $pageNumber + '.png')
            $bitmap.Save($pngPath, [System.Drawing.Imaging.ImageFormat]::Png)
            Write-Output $pngPath
        }
        finally {
            $graphics.Dispose()
            $bitmap.Dispose()
            $metafile.Dispose()
            $stream.Dispose()
            [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($page)
        }
    }
}
finally {
    if ($null -ne $document) {
        $saveChanges = 0
        $document.Close([ref]$saveChanges)
        [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($document)
    }
    if ($null -ne $word) {
        $word.Quit()
        [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($word)
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
