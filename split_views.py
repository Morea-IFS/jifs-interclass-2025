"""
Script para extrair funções do views.py monolítico e criar módulos separados.
Executa uma vez e depois é descartado.
"""
import re, os, textwrap

VIEWS_PY = r'app\views.py'
VIEWS_DIR = r'app\views'

# Lê o arquivo original
with open(VIEWS_PY, 'r', encoding='utf-8') as f:
    full = f.read()

lines = full.split('\n')

# Encontra todas as funções de nível superior (def no início da linha)
func_ranges = []
for i, line in enumerate(lines):
    m = re.match(r'^def (\w+)\(', line)
    if m:
        func_ranges.append((m.group(1), i))

# Para cada função, determina onde começa (incluindo decoradores acima) e onde termina
def get_func_block(func_name, start_idx):
    """Retorna (real_start, end) incluindo decoradores acima."""
    # Procura decoradores acima
    real_start = start_idx
    j = start_idx - 1
    while j >= 0:
        stripped = lines[j].strip()
        if stripped.startswith('@') or stripped == '':
            if stripped.startswith('@'):
                real_start = j
            j -= 1
        else:
            break
    
    # Procura fim da função (próximo def no nível superior ou EOF)
    end = len(lines)
    for i in range(start_idx + 1, len(lines)):
        # Próxima definição de função ou classe no nível superior
        if re.match(r'^(def |class |@)', lines[i]) and not lines[i].startswith(' '):
            # Verifica se é um decorator - se for, faz parte da próxima função
            if lines[i].strip().startswith('@'):
                end = i
                break
            else:
                end = i
                break
    
    return real_start, end

# Mapeamento de qual módulo cada função vai
MODULE_MAP = {
    'public.py': [
        'events_list', 'home_public', 'home_admin', 'switching_public', 
        'about_us', 'authenticate_file',
    ],
    'matches.py': [
        'matches_manage', 'matches_edit', 'games', 'match_settings',
        'players_in_teams', 'players_match', 'add_players_match',
    ],
    'scoreboard.py': [
        'scoreboard', 'scoreboard_public', 'scoreboard_projector',
    ],
    'settings_views.py': [
        'settings', 'settings_new', 'theme_manage',
        'banner_register', 'banner_manage', 
        'statement_register', 'statement_manage',
        'chefe_manage', 'faq_manage', 'faq_register',
        'anexo_manage', 'anexo_register',
        'enrollment_manage', 'enrollment_register',
        'attachments',
    ],
    'generators.py': [
        'generator_badge', 'generator_certificate', 'generator_data',
        'generator_spreadsheet', 'generate_spreadsheet',
    ],
    'dashboard.py': [
        'dashboard_acesso', 'dashboard_acesso_user_detail',
        '_has_user_document', '_format_dt', '_get_user_access_qs',
        '_build_user_dashboard_row',
    ],
}

# Funções que já existem nos módulos criados (não extrair de novo)
ALREADY_DONE = {
    'login', 'sair', 'upload_document', 'boss_data', 'terms_use',
    'has_accepted_terms',  # auth.py
    'player_manage', 'player_edit',  # players.py
    'team_manage', 'team_edit', 'team_players_manage', 'add_player_team',  # teams.py
    'event_manage', 'event_sport_manage', 'event_sport_edit',  # events.py
    'voluntary_manage',  # volunteers.py
    'user_manage', 'manage_session',  # users.py
    'get_teams', 'get_sexos', 'get_groups', 'search_player_preview',  # api.py
    'page_in_erro404', 'erro_403_customizado', 'erro_404_customizado',  # errors.py
    # Funções utilitárias que foram movidas para helpers.py
    'verificar_foto', 'type_file', 'calcular_idade', 'generate_authenticity',
    # Funções privadas de acesso
    '_acesso_evento', '_acesso_team', '_acesso_team_sport', '_acesso_player', '_acesso_match',
    '_check_gender_compatibility', '_player_queryset_for_team',
}

# Coleta imports do topo do arquivo (primeiras ~50 linhas)
import_lines = []
for line in lines[:50]:
    stripped = line.strip()
    if stripped.startswith(('import ', 'from ')):
        import_lines.append(line.rstrip())

COMMON_IMPORTS = '\n'.join(import_lines)

# Extrai e salva cada módulo
for module_file, func_names in MODULE_MAP.items():
    filepath = os.path.join(VIEWS_DIR, module_file)
    
    # Pula se já existe
    if os.path.exists(filepath):
        print(f"SKIP: {filepath} já existe")
        continue
    
    blocks = []
    for func_name in func_names:
        if func_name in ALREADY_DONE:
            continue
        # Encontra a função
        for name, idx in func_ranges:
            if name == func_name:
                start, end = get_func_block(name, idx)
                block = '\n'.join(lines[start:end]).rstrip()
                blocks.append(block)
                print(f"  Extraído: {func_name} (linhas {start+1}-{end})")
                break
        else:
            print(f"  AVISO: {func_name} não encontrada no views.py")
    
    if blocks:
        # Monta arquivo com imports + funções
        content = f'"""\nViews extraídas automaticamente do views.py monolítico.\nMódulo: {module_file}\n"""\n\n'
        content += COMMON_IMPORTS + '\n\n'
        content += '# Imports locais do projeto\n'
        content += 'from app.helpers import (\n'
        content += '    acesso_evento, acesso_team, acesso_team_sport,\n'
        content += '    acesso_player, acesso_match, verificar_foto,\n'
        content += '    type_file, calcular_idade, generate_authenticity,\n'
        content += '    check_gender_compatibility, player_queryset_for_team,\n'
        content += '    SEXO_NAMES,\n'
        content += ')\n'
        content += 'from app.services.pdf import build_pdf_context, generate_pdf_response, generate_qr_base64\n'
        content += 'from app.services.points import calculate_points, calculate_penalties_count, get_aces_count\n'
        content += 'from app.services.volleyball import get_ordered_team_matches, get_ordered_sets\n'
        content += 'from app.services.password import generate_random_password\n\n'
        content += '\n\n'.join(blocks)
        content += '\n'
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"CRIADO: {filepath} ({len(blocks)} funções)")
    else:
        print(f"VAZIO: {module_file} - nenhuma função para extrair")

print("\n=== Extração concluída ===")
print("Agora crie o __init__.py e atualize o urls.py")
