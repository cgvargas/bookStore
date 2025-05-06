# find_template_usage.ps1
# Script para encontrar todas as referências a um template específico no projeto Django
# e CSS relacionados aos elementos do template

$templateName = "modal_prateleiras.html"
$projectRoot = Get-Location

# Elementos específicos do modal para buscar em arquivos CSS
$cssSelectors = @(
    "prateleirasModal",
    "prateleirasCarousel",
    "modal-prateleiras",
    "#prateleirasModal",
    ".carousel-prateleiras"
)

Write-Host "Buscando referencias ao template: $templateName"
Write-Host "==============================================================="

# Buscar em arquivos Python
Write-Host "`nBuscando em arquivos Python (.py):"
$pyResults = Get-ChildItem -Path $projectRoot -Recurse -Include "*.py" |
           Where-Object { $_.FullName -notlike "*\node_modules\*" } |
           Select-String -Pattern $templateName -SimpleMatch

$pyCount = 0
if ($pyResults) {
    $previousPath = ""
    foreach ($result in $pyResults) {
        if ($result.Path -notlike "*$templateName") {
            $pyCount++
            if ($result.Path -ne $previousPath) {
                Write-Host "Arquivo: $($result.Path)" -ForegroundColor Yellow
                $previousPath = $result.Path
            }
            Write-Host "  Linha $($result.LineNumber): $($result.Line.Trim())"
        }
    }
}

if ($pyCount -eq 0) {
    Write-Host "  Nenhuma referencia encontrada em arquivos Python."
} else {
    Write-Host "  Total de referencias em arquivos Python: $pyCount"
}

# Buscar em arquivos HTML
Write-Host "`nBuscando em arquivos de template (.html):"
$htmlResults = Get-ChildItem -Path $projectRoot -Recurse -Include "*.html" |
             Where-Object { $_.FullName -notlike "*\node_modules\*" } |
             Select-String -Pattern $templateName -SimpleMatch

$htmlCount = 0
if ($htmlResults) {
    $previousPath = ""
    foreach ($result in $htmlResults) {
        if ($result.Path -notlike "*$templateName") {
            $htmlCount++
            if ($result.Path -ne $previousPath) {
                Write-Host "Arquivo: $($result.Path)" -ForegroundColor Yellow
                $previousPath = $result.Path
            }
            Write-Host "  Linha $($result.LineNumber): $($result.Line.Trim())"
        }
    }
}

if ($htmlCount -eq 0) {
    Write-Host "  Nenhuma referencia encontrada em arquivos HTML."
} else {
    Write-Host "  Total de referencias em arquivos HTML: $htmlCount"
}

# Buscar em arquivos CSS por seletores relacionados ao modal
Write-Host "`nBuscando estilos CSS relacionados ao modal de prateleiras:"
$cssResults = @()

foreach ($selector in $cssSelectors) {
    $results = Get-ChildItem -Path $projectRoot -Recurse -Include "*.css" |
              Where-Object { $_.FullName -notlike "*\node_modules\*" } |
              Select-String -Pattern $selector -SimpleMatch

    if ($results) {
        $cssResults += $results
    }
}

# Também buscar por estilos relacionados a modais e carousels em geral
$generalResults = Get-ChildItem -Path $projectRoot -Recurse -Include "*.css" |
                 Where-Object { $_.FullName -notlike "*\node_modules\*" } |
                 Select-String -Pattern "\.modal-body|\.carousel|\.modal " -SimpleMatch

if ($generalResults) {
    Write-Host "`n  Arquivos CSS com estilos gerais para modais e carousels:"
    $previousPath = ""
    foreach ($result in $generalResults) {
        if ($result.Path -ne $previousPath) {
            Write-Host "  Arquivo: $($result.Path)" -ForegroundColor Yellow
            $previousPath = $result.Path
        }
    }
}

$cssCount = ($cssResults | Select-Object Path -Unique).Count
if ($cssCount -eq 0) {
    Write-Host "  Nenhum arquivo CSS com seletores especificos para o modal de prateleiras."
} else {
    Write-Host "`n  Arquivos CSS com seletores especificos para o modal de prateleiras:"
    $previousPath = ""
    foreach ($result in $cssResults) {
        if ($result.Path -ne $previousPath) {
            Write-Host "  Arquivo: $($result.Path)" -ForegroundColor Yellow
            $previousPath = $result.Path
        }
        Write-Host "    Linha $($result.LineNumber): $($result.Line.Trim())"
    }
    Write-Host "  Total de arquivos CSS com seletores especificos: $cssCount"
}

# Verificar estilos inline no próprio template
Write-Host "`nVerificando estilos inline no proprio template modal_prateleiras.html:"
$inlineStyles = Get-ChildItem -Path $projectRoot -Recurse -Filter "modal_prateleiras.html" |
               Select-String -Pattern "style=" -SimpleMatch

if ($inlineStyles) {
    Write-Host "  Estilos inline encontrados no template:"
    foreach ($style in $inlineStyles) {
        Write-Host "    Linha $($style.LineNumber): $($style.Line.Trim())"
    }
} else {
    Write-Host "  Nenhum estilo inline encontrado no template."
}

# Totais
$totalCount = $pyCount + $htmlCount
Write-Host "`n==============================================================="
if ($totalCount -eq 0) {
    Write-Host "Nenhuma refereência ao template '$templateName' foi encontrada no projeto."
} else {
    Write-Host "Total de referencias encontradas: $totalCount"
}
Write-Host "Busca concluida!"