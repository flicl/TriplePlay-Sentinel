#!/bin/bash

# 🔗 TriplePlay-Sentinel - Link Checker Script
# Script para verificar e validar todos os links na documentação

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configurações
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCS_DIR="${PROJECT_ROOT}/docs"
GITHUB_REPO="flicl/TriplePlay-Sentinel"
BASE_URL="https://github.com/${GITHUB_REPO}"

# Função para log colorido
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_header() {
    echo -e "${BLUE}$1${NC}"
}

# Função para verificar se arquivo existe
check_file_exists() {
    local file="$1"
    if [ ! -f "$file" ]; then
        log_error "Arquivo não encontrado: $file"
        return 1
    fi
    return 0
}

# Verificar links relativos da documentação
check_relative_links() {
    log_header "🔍 Verificando links relativos da documentação..."
    
    local broken_links=0
    
    # Encontrar todos os arquivos markdown
    while IFS= read -r -d '' file; do
        log "Verificando: $(basename "$file")"
        
        # Extrair links relativos markdown [texto](caminho.md)
        grep -oE '\[([^]]+)\]\(([^)]+\.md[^)]*)\)' "$file" | while read -r link; do
            # Extrair o caminho do link
            local path=$(echo "$link" | sed -E 's/.*\(([^)]+)\).*/\1/')
            
            # Resolver caminho relativo
            local file_dir=$(dirname "$file")
            local full_path=$(realpath "$file_dir/$path" 2>/dev/null || echo "INVALID")
            
            if [ "$full_path" = "INVALID" ] || [ ! -f "$full_path" ]; then
                log_error "Link quebrado em $(basename "$file"): $path"
                ((broken_links++))
            fi
        done
        
    done < <(find "$DOCS_DIR" -name "*.md" -print0)
    
    if [ $broken_links -eq 0 ]; then
        log "✅ Todos os links relativos estão funcionando"
    else
        log_error "❌ Encontrados $broken_links links quebrados"
    fi
    
    return $broken_links
}

# Verificar consistência de URLs GitHub
check_github_urls() {
    log_header "🐙 Verificando URLs do GitHub..."
    
    local inconsistent=0
    
    # Procurar por URLs do GitHub
    while IFS= read -r -d '' file; do
        # Procurar por URLs github.com
        local github_urls=$(grep -oE 'https://github\.com/[^/]+/[^/\s]+' "$file" 2>/dev/null || true)
        
        if [ -n "$github_urls" ]; then
            while read -r url; do
                if [[ "$url" != "$BASE_URL"* ]]; then
                    log_warn "URL GitHub inconsistente em $(basename "$file"): $url"
                    log_warn "  Esperado: $BASE_URL"
                    ((inconsistent++))
                fi
            done <<< "$github_urls"
        fi
        
    done < <(find "$PROJECT_ROOT" -name "*.md" -print0)
    
    if [ $inconsistent -eq 0 ]; then
        log "✅ URLs do GitHub estão consistentes"
    else
        log_warn "⚠️  Encontradas $inconsistent URLs inconsistentes"
    fi
    
    return $inconsistent
}

# Verificar endpoints da API
check_api_endpoints() {
    log_header "🔌 Verificando endpoints da API..."
    
    local incorrect=0
    local correct_endpoints=(
        "/api/health"
        "/api/test"
        "/api/connection-test"
        "/api/stats"
        "/api/cache"
    )
    
    # Procurar por endpoints incorretos (com versioning)
    while IFS= read -r -d '' file; do
        # Procurar por /api/v1/ que não deveria existir
        local v1_endpoints=$(grep -oE '/api/v1/[^"\s]+' "$file" 2>/dev/null || true)
        
        if [ -n "$v1_endpoints" ]; then
            while read -r endpoint; do
                log_error "Endpoint incorreto em $(basename "$file"): $endpoint"
                log_error "  Remover 'v1' do endpoint"
                ((incorrect++))
            done <<< "$v1_endpoints"
        fi
        
    done < <(find "$DOCS_DIR" -name "*.md" -print0)
    
    if [ $incorrect -eq 0 ]; then
        log "✅ Endpoints da API estão corretos"
    else
        log_error "❌ Encontrados $incorrect endpoints incorretos"
    fi
    
    return $incorrect
}

# Verificar localhost URLs
check_localhost_urls() {
    log_header "🏠 Verificando URLs localhost..."
    
    local count=0
    
    while IFS= read -r -d '' file; do
        local localhost_urls=$(grep -oE 'http://localhost:[0-9]+[^"\s]*' "$file" 2>/dev/null || true)
        
        if [ -n "$localhost_urls" ]; then
            while read -r url; do
                ((count++))
                # Verificar se é a porta padrão 5000
                if [[ "$url" != *":5000"* ]]; then
                    log_warn "URL localhost não padrão em $(basename "$file"): $url"
                fi
            done <<< "$localhost_urls"
        fi
        
    done < <(find "$PROJECT_ROOT" -name "*.md" -print0)
    
    log "📊 Encontradas $count URLs localhost na documentação"
}

# Gerar relatório de links
generate_link_report() {
    log_header "📊 Gerando relatório de links..."
    
    local report_file="${PROJECT_ROOT}/link_report.md"
    
    cat > "$report_file" << EOF
# Relatório de Links - TriplePlay-Sentinel

Gerado em: $(date)

## 📈 Estatísticas

EOF
    
    # Contar tipos de links
    local md_links=$(find "$PROJECT_ROOT" -name "*.md" -exec grep -oE '\[([^]]+)\]\(([^)]+)\)' {} \; | wc -l)
    local github_links=$(find "$PROJECT_ROOT" -name "*.md" -exec grep -oE 'https://github\.com/[^/\s]+' {} \; | wc -l)
    local localhost_links=$(find "$PROJECT_ROOT" -name "*.md" -exec grep -oE 'http://localhost:[0-9]+' {} \; | wc -l)
    local api_links=$(find "$PROJECT_ROOT" -name "*.md" -exec grep -oE '/api/[^"\s]+' {} \; | wc -l)
    
    cat >> "$report_file" << EOF
- **Total de links markdown**: $md_links
- **Links do GitHub**: $github_links
- **URLs localhost**: $localhost_links
- **Endpoints de API**: $api_links

## 🔗 Links Encontrados

### Links do GitHub
\`\`\`
EOF
    
    find "$PROJECT_ROOT" -name "*.md" -exec grep -oE 'https://github\.com/[^/\s]+/[^/\s]+' {} \; | sort | uniq >> "$report_file"
    
    cat >> "$report_file" << EOF
\`\`\`

### Endpoints da API
\`\`\`
EOF
    
    find "$PROJECT_ROOT" -name "*.md" -exec grep -oE '/api/[^"\s]+' {} \; | sort | uniq >> "$report_file"
    
    cat >> "$report_file" << EOF
\`\`\`

---
*Relatório gerado automaticamente pelo link-checker script*
EOF
    
    log "📄 Relatório salvo em: $report_file"
}

# Função principal
main() {
    log_header "🚀 TriplePlay-Sentinel Link Checker"
    echo "======================================"
    echo
    
    cd "$PROJECT_ROOT"
    
    local total_issues=0
    
    # Executar verificações
    check_relative_links
    total_issues=$((total_issues + $?))
    
    echo
    check_github_urls
    total_issues=$((total_issues + $?))
    
    echo
    check_api_endpoints
    total_issues=$((total_issues + $?))
    
    echo
    check_localhost_urls
    
    echo
    generate_link_report
    
    echo
    log_header "📋 Resumo Final"
    if [ $total_issues -eq 0 ]; then
        log "🎉 Todos os links estão funcionando corretamente!"
    else
        log_error "⚠️  Encontrados $total_issues problemas que precisam ser corrigidos"
    fi
    
    return $total_issues
}

# Verificar se deve executar
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi