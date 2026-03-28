<?php
/**
 * API IPTV com suporte a Xtream Codes
 * Autor: Josiel Jefferson
 * Versão: 1.0
 */

// Configurações
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

// Credenciais
define('USERNAME', 'josielluz');
define('PASSWORD', '3264717');

// Parâmetros recebidos
$user = $_GET['username'] ?? '';
$pass = $_GET['password'] ?? '';
$action = $_GET['action'] ?? '';
$type = $_GET['type'] ?? '';
$output = $_GET['output'] ?? '';

// Autenticação
if ($user !== USERNAME || $pass !== PASSWORD) {
    http_response_code(401);
    echo json_encode([
        'error' => 'Acesso negado',
        'code' => 401,
        'message' => 'Credenciais inválidas'
    ]);
    exit;
}

// Caminho do arquivo M3U
$m3u_file = __DIR__ . '/../docs/playlists.m3u';
$channels_file = __DIR__ . '/../docs/channels.json';

// Verificar se arquivo existe
if (!file_exists($m3u_file)) {
    http_response_code(404);
    echo json_encode([
        'error' => 'Playlist não encontrada',
        'code' => 404,
        'message' => 'Arquivo de playlist não disponível'
    ]);
    exit;
}

/**
 * Função para obter informações do servidor
 */
function getServerInfo() {
    $protocol = isset($_SERVER['HTTPS']) && $_SERVER['HTTPS'] === 'on' ? 'https' : 'http';
    $host = $_SERVER['HTTP_HOST'];
    $url = $protocol . '://' . $host;
    
    return [
        'server_name' => 'IPTV System - Josiel Jefferson',
        'url' => $url,
        'port' => 80,
        'https_port' => 443,
        'server_protocol' => $protocol,
        'timestamp_now' => time(),
        'time_now' => date('Y-m-d H:i:s'),
        'timezone' => 'America/Fortaleza',
        'api_version' => '1.0',
        'xtream_codes' => true
    ];
}

/**
 * Função para obter lista de canais
 */
function getChannels($m3u_file, $channels_file) {
    // Tentar ler do cache JSON primeiro
    if (file_exists($channels_file)) {
        $json_data = file_get_contents($channels_file);
        $channels = json_decode($json_data, true);
        if ($channels && count($channels) > 0) {
            return $channels;
        }
    }
    
    // Se não tiver cache, processar M3U
    $channels = [];
    $content = file_get_contents($m3u_file);
    $lines = explode("\n", $content);
    $stream_id = 1;
    
    for ($i = 0; $i < count($lines); $i++) {
        $line = trim($lines[$i]);
        
        if (strpos($line, '#EXTINF') !== false) {
            // Extrair atributos
            preg_match('/tvg-id="([^"]*)"/', $line, $tvg_id);
            preg_match('/tvg-name="([^"]*)"/', $line, $tvg_name);
            preg_match('/tvg-logo="([^"]*)"/', $line, $tvg_logo);
            preg_match('/group-title="([^"]*)"/', $line, $group);
            preg_match('/,(.*)$/', $line, $name);
            
            // Próxima linha é a URL
            $url = isset($lines[$i + 1]) ? trim($lines[$i + 1]) : '';
            
            if (!empty($url)) {
                $channels[] = [
                    'stream_id' => $stream_id++,
                    'num' => $stream_id - 1,
                    'name' => trim($name[1] ?? 'Sem Nome'),
                    'stream_type' => 'live',
                    'stream_icon' => $tvg_logo[1] ?? '',
                    'epg_channel_id' => $tvg_id[1] ?? '',
                    'added' => date('Y-m-d H:i:s'),
                    'category_id' => 1,
                    'category_name' => $group[1] ?? 'Geral',
                    'url' => $url,
                    'tvg_name' => $tvg_name[1] ?? '',
                    'tvg_logo' => $tvg_logo[1] ?? '',
                    'tvg_id' => $tvg_id[1] ?? ''
                ];
            }
        }
    }
    
    return $channels;
}

/**
 * Função para obter categorias
 */
function getCategories($channels) {
    $categories = [];
    $category_id = 1;
    
    foreach ($channels as $channel) {
        $cat_name = $channel['category_name'];
        
        $found = false;
        foreach ($categories as $cat) {
            if ($cat['category_name'] === $cat_name) {
                $found = true;
                break;
            }
        }
        
        if (!$found) {
            $categories[] = [
                'category_id' => $category_id++,
                'category_name' => $cat_name,
                'parent_id' => 0
            ];
        }
    }
    
    return $categories;
}

// Rotas da API Xtream Codes
$channels = getChannels($m3u_file, $channels_file);
$categories = getCategories($channels);

// Rota: informações do servidor
if ($action === 'server_info' || $action === 'get_server_info') {
    echo json_encode(getServerInfo());
    exit;
}

// Rota: lista de categorias
if ($action === 'get_categories') {
    echo json_encode($categories);
    exit;
}

// Rota: lista de canais
if ($action === 'get_channels' || $action === 'get_live_streams') {
    echo json_encode($channels);
    exit;
}

// Rota: lista de canais por categoria
if ($action === 'get_live_streams_by_category') {
    $category = $_GET['category'] ?? '';
    $filtered = array_filter($channels, function($channel) use ($category) {
        return $channel['category_name'] === $category;
    });
    echo json_encode(array_values($filtered));
    exit;
}

// Rota: detalhes do canal
if ($action === 'get_stream_info') {
    $stream_id = $_GET['stream_id'] ?? 0;
    $found = null;
    
    foreach ($channels as $channel) {
        if ($channel['stream_id'] == $stream_id) {
            $found = $channel;
            break;
        }
    }
    
    if ($found) {
        echo json_encode($found);
    } else {
        http_response_code(404);
        echo json_encode(['error' => 'Canal não encontrado']);
    }
    exit;
}

// Rota: player de stream
if ($action === 'play') {
    $stream_id = $_GET['stream_id'] ?? 0;
    
    foreach ($channels as $channel) {
        if ($channel['stream_id'] == $stream_id) {
            header('Location: ' . $channel['url']);
            exit;
        }
    }
    
    http_response_code(404);
    echo json_encode(['error' => 'Stream não encontrada']);
    exit;
}

// Rota: playlist M3U
if ($type === 'm3u_plus' || $type === 'm3u8' || $output === 'ts') {
    header('Content-Type: application/vnd.apple.mpegurl');
    header('Content-Disposition: attachment; filename="playlist.m3u"');
    readfile($m3u_file);
    exit;
}

// Rota: playlist em formato JSON
if ($action === 'get_playlist_json') {
    echo json_encode($channels);
    exit;
}

// Rota padrão: documentação
echo json_encode([
    'status' => 'online',
    'server' => 'IPTV System',
    'version' => '1.0',
    'author' => 'Josiel Jefferson',
    'email' => 'josielluz@proton.me',
    'endpoints' => [
        [
            'name' => 'Server Info',
            'url' => '/api/get.php?username=josielluz&password=3264717&action=server_info'
        ],
        [
            'name' => 'Categories',
            'url' => '/api/get.php?username=josielluz&password=3264717&action=get_categories'
        ],
        [
            'name' => 'Channels',
            'url' => '/api/get.php?username=josielluz&password=3264717&action=get_channels'
        ],
        [
            'name' => 'Playlist M3U',
            'url' => '/api/get.php?username=josielluz&password=3264717&type=m3u_plus'
        ],
        [
            'name' => 'Xtream Codes Format',
            'url' => '/api/get.php?username=josielluz&password=3264717&type=m3u_plus&output=ts'
        ]
    ],
    'xtream_codes_compatible' => true,
    'documentation' => 'https://github.com/josieljefferson/jeffersondplay'
], JSON_PRETTY_PRINT);
?>