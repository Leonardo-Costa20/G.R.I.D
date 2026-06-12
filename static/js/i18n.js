// ── G.R.I.D Shared i18n ─────────────────────────────────────────────────────
// Lê grid_lang do localStorage e aplica traduções ao carregar a página.
// Cada template chama applyPageLang(pageId) no seu $(document).ready().

const GRID_I18N = {
    pt: {
        // Sidebar
        nav_camera: 'Câmera', nav_sensors: 'Sensores', nav_autotile: 'Auto Tile',
        nav_joystick: 'Joystick', nav_dashboard: 'Dashboard', nav_logs: 'Mission Logs',
        nav_admin: 'Admin', nav_settings: 'Definições', nav_theme: 'Interface Color', nav_logout: 'Sair',
        // Topbar comum
        session_as: 'Sessão activa como:',
        // Dashboard
        dash_title: 'G.R.I.D OS // Dashboard',
        dash_awaiting: 'A AGUARDAR',
        dash_online: 'ROVER ONLINE',
        dash_offline: 'ROVER OFFLINE',
        // Dashboard bottom nav (mobile)
        bnav_camera: 'Câmera', bnav_sensors: 'Sensores', bnav_theme: 'Tema',
        bnav_settings: 'Definições', bnav_logout: 'Sair',
        // Dashboard sensor drawer
        sensor_gas: 'Gás', sensor_temp: 'Temperatura', sensor_pressure: 'Pressão',
        sensor_altitude: 'Altitude', sensor_tilt: 'Tilt',
        // Joystick window
        joy_title: 'Joystick de Controlo', joy_forward: 'Frente', joy_back: 'Ré',
        joy_left: 'Esq', joy_right: 'Dir', joy_stop: 'STOP',
        // Admin
        admin_title: 'G.R.I.D OS // Admin Panel',
        admin_awaiting: 'A AGUARDAR...',
        admin_active_accounts: 'Contas Ativas', admin_equipment: 'Equipamentos',
        admin_infra: 'Infraestrutura', admin_online_users: 'Utilizadores Online',
        admin_permissions: 'Gestão de Permissões',
        admin_member: 'Membro', admin_status: 'Estado', admin_role: 'Cargo',
        admin_rover_linked: 'Rover Vinculado', admin_action: 'Ação',
        admin_active: 'Ativo', admin_blocked: 'Bloqueada', admin_pending: 'Pendente',
        admin_block: '🔒 Bloquear', admin_unblock: '🔓 Desbloquear', admin_remove: 'Remover',
        admin_rovers: 'Gestão de Rovers',
        admin_rover_loading: 'A carregar rovers...', admin_rover_error: 'Erro ao carregar rovers.',
        admin_rover_none: 'Nenhum rover registado.',
        admin_rover_linked_badge: 'Vinculado', admin_rover_pending_badge: 'Pendente',
        admin_register_rover: '+ Registar Rover',
        admin_analytics: 'Database & Site Analytics',
        admin_mqtt_total: 'Total Pacotes MQTT', admin_logs_total: 'Total Logs Coletados',
        admin_db_speed: 'Velocidade Supabase',
        admin_live_logs: 'Live Access Logs',
        admin_sys_kernel: '[SYS] Kernel operacional.',
        admin_sys_mqtt: '[SYS] Ligação MQTT em escuta estável.',
        // Logs
        logs_title: 'G.R.I.D OS // Mission Logs',
        logs_total: 'Total de Registos', logs_page: 'Página Atual',
        logs_sensors_avail: 'Sensores Disponíveis', logs_last_update: 'Última Actualização',
        logs_sensor_label: 'Sensor', logs_start_label: 'Data Início', logs_end_label: 'Data Fim',
        logs_clear: 'Limpar Filtros',
        logs_table_title: 'Registos da Missão', logs_loading: 'A carregar...',
        logs_all_sensors: 'Todos os Sensores',
        logs_alert: 'Alerta', logs_timestamp: 'Timestamp', logs_value: 'Valor',
        logs_message: 'Mensagem', logs_category: 'Categoria',
        logs_sync: 'A sincronizar com a base de dados...',
    },
    en: {
        nav_camera: 'Camera', nav_sensors: 'Sensors', nav_autotile: 'Auto Tile',
        nav_joystick: 'Joystick', nav_dashboard: 'Dashboard', nav_logs: 'Mission Logs',
        nav_admin: 'Admin', nav_settings: 'Settings', nav_theme: 'Interface Color', nav_logout: 'Logout',
        session_as: 'Active session as:',
        dash_title: 'G.R.I.D OS // Dashboard',
        dash_awaiting: 'AWAITING',
        dash_online: 'ROVER ONLINE',
        dash_offline: 'ROVER OFFLINE',
        bnav_camera: 'Camera', bnav_sensors: 'Sensors', bnav_theme: 'Theme',
        bnav_settings: 'Settings', bnav_logout: 'Logout',
        sensor_gas: 'Gas', sensor_temp: 'Temperature', sensor_pressure: 'Pressure',
        sensor_altitude: 'Altitude', sensor_tilt: 'Tilt',
        joy_title: 'Control Joystick', joy_forward: 'Fwd', joy_back: 'Rev',
        joy_left: 'Left', joy_right: 'Right', joy_stop: 'STOP',
        admin_title: 'G.R.I.D OS // Admin Panel',
        admin_awaiting: 'AWAITING...',
        admin_active_accounts: 'Active Accounts', admin_equipment: 'Equipment',
        admin_infra: 'Infrastructure', admin_online_users: 'Online Users',
        admin_permissions: 'Permission Management',
        admin_member: 'Member', admin_status: 'Status', admin_role: 'Role',
        admin_rover_linked: 'Linked Rover', admin_action: 'Action',
        admin_active: 'Active', admin_blocked: 'Blocked', admin_pending: 'Pending',
        admin_block: '🔒 Block', admin_unblock: '🔓 Unblock', admin_remove: 'Remove',
        admin_rovers: 'Rover Management',
        admin_rover_loading: 'Loading rovers...', admin_rover_error: 'Error loading rovers.',
        admin_rover_none: 'No rovers registered.',
        admin_rover_linked_badge: 'Linked', admin_rover_pending_badge: 'Pending',
        admin_register_rover: '+ Register Rover',
        admin_analytics: 'Database & Site Analytics',
        admin_mqtt_total: 'Total MQTT Packets', admin_logs_total: 'Total Logs Collected',
        admin_db_speed: 'Supabase Speed',
        admin_live_logs: 'Live Access Logs',
        admin_sys_kernel: '[SYS] Kernel operational.',
        admin_sys_mqtt: '[SYS] Stable MQTT connection listening.',
        logs_title: 'G.R.I.D OS // Mission Logs',
        logs_total: 'Total Records', logs_page: 'Current Page',
        logs_sensors_avail: 'Available Sensors', logs_last_update: 'Last Update',
        logs_sensor_label: 'Sensor', logs_start_label: 'Start Date', logs_end_label: 'End Date',
        logs_clear: 'Clear Filters',
        logs_table_title: 'Mission Records', logs_loading: 'Loading...',
        logs_all_sensors: 'All Sensors',
        logs_alert: 'Alert', logs_timestamp: 'Timestamp', logs_value: 'Value',
        logs_message: 'Message', logs_category: 'Category',
        logs_sync: 'Syncing with database...',
    },
    es: {
        nav_camera: 'Cámara', nav_sensors: 'Sensores', nav_autotile: 'Auto Tile',
        nav_joystick: 'Joystick', nav_dashboard: 'Dashboard', nav_logs: 'Registros',
        nav_admin: 'Admin', nav_settings: 'Configuración', nav_theme: 'Color Interfaz', nav_logout: 'Salir',
        session_as: 'Sesión activa como:',
        dash_title: 'G.R.I.D OS // Dashboard',
        dash_awaiting: 'EN ESPERA',
        dash_online: 'ROVER EN LÍNEA',
        dash_offline: 'ROVER FUERA DE LÍNEA',
        bnav_camera: 'Cámara', bnav_sensors: 'Sensores', bnav_theme: 'Tema',
        bnav_settings: 'Config.', bnav_logout: 'Salir',
        sensor_gas: 'Gas', sensor_temp: 'Temperatura', sensor_pressure: 'Presión',
        sensor_altitude: 'Altitud', sensor_tilt: 'Inclinación',
        joy_title: 'Joystick de Control', joy_forward: 'Adelante', joy_back: 'Atrás',
        joy_left: 'Izq', joy_right: 'Der', joy_stop: 'STOP',
        admin_title: 'G.R.I.D OS // Panel Admin',
        admin_awaiting: 'EN ESPERA...',
        admin_active_accounts: 'Cuentas Activas', admin_equipment: 'Equipos',
        admin_infra: 'Infraestructura', admin_online_users: 'Usuarios Online',
        admin_permissions: 'Gestión de Permisos',
        admin_member: 'Miembro', admin_status: 'Estado', admin_role: 'Cargo',
        admin_rover_linked: 'Rover Vinculado', admin_action: 'Acción',
        admin_active: 'Activo', admin_blocked: 'Bloqueada', admin_pending: 'Pendiente',
        admin_block: '🔒 Bloquear', admin_unblock: '🔓 Desbloquear', admin_remove: 'Eliminar',
        admin_rovers: 'Gestión de Rovers',
        admin_rover_loading: 'Cargando rovers...', admin_rover_error: 'Error al cargar rovers.',
        admin_rover_none: 'Ningún rover registrado.',
        admin_rover_linked_badge: 'Vinculado', admin_rover_pending_badge: 'Pendiente',
        admin_register_rover: '+ Registrar Rover',
        admin_analytics: 'Base de Datos y Analíticas',
        admin_mqtt_total: 'Total Paquetes MQTT', admin_logs_total: 'Total Registros',
        admin_db_speed: 'Velocidad Supabase',
        admin_live_logs: 'Registros de Acceso',
        admin_sys_kernel: '[SYS] Kernel operacional.',
        admin_sys_mqtt: '[SYS] Conexión MQTT escuchando.',
        logs_title: 'G.R.I.D OS // Registros de Misión',
        logs_total: 'Total Registros', logs_page: 'Página Actual',
        logs_sensors_avail: 'Sensores Disponibles', logs_last_update: 'Última Actualización',
        logs_sensor_label: 'Sensor', logs_start_label: 'Fecha Inicio', logs_end_label: 'Fecha Fin',
        logs_clear: 'Limpiar Filtros',
        logs_table_title: 'Registros de Misión', logs_loading: 'Cargando...',
        logs_all_sensors: 'Todos los Sensores',
        logs_alert: 'Alerta', logs_timestamp: 'Timestamp', logs_value: 'Valor',
        logs_message: 'Mensaje', logs_category: 'Categoría',
        logs_sync: 'Sincronizando con la base de datos...',
    },
    fr: {
        nav_camera: 'Caméra', nav_sensors: 'Capteurs', nav_autotile: 'Auto Tile',
        nav_joystick: 'Joystick', nav_dashboard: 'Dashboard', nav_logs: 'Journaux',
        nav_admin: 'Admin', nav_settings: 'Paramètres', nav_theme: 'Couleur Interface', nav_logout: 'Déconnexion',
        session_as: 'Session active en tant que:',
        dash_title: 'G.R.I.D OS // Dashboard',
        dash_awaiting: 'EN ATTENTE',
        dash_online: 'ROVER EN LIGNE',
        dash_offline: 'ROVER HORS LIGNE',
        bnav_camera: 'Caméra', bnav_sensors: 'Capteurs', bnav_theme: 'Thème',
        bnav_settings: 'Paramètres', bnav_logout: 'Quitter',
        sensor_gas: 'Gaz', sensor_temp: 'Température', sensor_pressure: 'Pression',
        sensor_altitude: 'Altitude', sensor_tilt: 'Inclinaison',
        joy_title: 'Joystick de Contrôle', joy_forward: 'Avant', joy_back: 'Arrière',
        joy_left: 'Gauche', joy_right: 'Droite', joy_stop: 'STOP',
        admin_title: 'G.R.I.D OS // Panneau Admin',
        admin_awaiting: 'EN ATTENTE...',
        admin_active_accounts: 'Comptes Actifs', admin_equipment: 'Équipements',
        admin_infra: 'Infrastructure', admin_online_users: 'Utilisateurs En Ligne',
        admin_permissions: 'Gestion des Permissions',
        admin_member: 'Membre', admin_status: 'Statut', admin_role: 'Rôle',
        admin_rover_linked: 'Rover Lié', admin_action: 'Action',
        admin_active: 'Actif', admin_blocked: 'Bloqué', admin_pending: 'En attente',
        admin_block: '🔒 Bloquer', admin_unblock: '🔓 Débloquer', admin_remove: 'Supprimer',
        admin_rovers: 'Gestion des Rovers',
        admin_rover_loading: 'Chargement rovers...', admin_rover_error: 'Erreur de chargement.',
        admin_rover_none: 'Aucun rover enregistré.',
        admin_rover_linked_badge: 'Lié', admin_rover_pending_badge: 'En attente',
        admin_register_rover: '+ Enregistrer Rover',
        admin_analytics: 'Base de Données & Analytiques',
        admin_mqtt_total: 'Total Paquets MQTT', admin_logs_total: 'Total Journaux',
        admin_db_speed: 'Vitesse Supabase',
        admin_live_logs: "Journaux d'Accès",
        admin_sys_kernel: '[SYS] Noyau opérationnel.',
        admin_sys_mqtt: '[SYS] Connexion MQTT stable en écoute.',
        logs_title: 'G.R.I.D OS // Journaux de Mission',
        logs_total: 'Total Enregistrements', logs_page: 'Page Actuelle',
        logs_sensors_avail: 'Capteurs Disponibles', logs_last_update: 'Dernière Mise à Jour',
        logs_sensor_label: 'Capteur', logs_start_label: 'Date Début', logs_end_label: 'Date Fin',
        logs_clear: 'Effacer Filtres',
        logs_table_title: 'Enregistrements de Mission', logs_loading: 'Chargement...',
        logs_all_sensors: 'Tous les Capteurs',
        logs_alert: 'Alerte', logs_timestamp: 'Horodatage', logs_value: 'Valeur',
        logs_message: 'Message', logs_category: 'Catégorie',
        logs_sync: 'Synchronisation avec la base de données...',
    }
};

function gridT(key) {
    const lang = localStorage.getItem('grid_lang') || 'pt';
    return (GRID_I18N[lang] || GRID_I18N['pt'])[key] || (GRID_I18N['pt'])[key] || key;
}

function applyPageLang(page) {
    const lang = localStorage.getItem('grid_lang') || 'pt';
    const t = GRID_I18N[lang] || GRID_I18N['pt'];

    // ── Sidebar (partilhada) ──────────────────────────────────────────────
    const setTxt = (sel, val) => { const el = document.querySelector(sel); if (el) el.textContent = val; };
    const setAllTxt = (sel, val) => document.querySelectorAll(sel).forEach(el => el.textContent = val);

    // Nav texts via data-i18n-nav attribute (adicionado nos templates)
    document.querySelectorAll('[data-i18n-nav]').forEach(el => {
        const key = el.getAttribute('data-i18n-nav');
        if (t[key]) el.textContent = t[key];
    });

    if (page === 'dashboard') {
        // Topbar title
        setTxt('.dash-header-title', t.dash_title);
        setTxt('.dash-session-label', t.session_as);
        // Rover status badge
        const st = document.getElementById('rover-status-text');
        if (st && (st.textContent === 'A AGUARDAR' || st.textContent === 'AWAITING' || st.textContent === 'EN ESPERA' || st.textContent === 'EN ATTENTE'))
            st.textContent = t.dash_awaiting;
        // Mobile bottom nav
        setTxt('.bnav-camera-label',   t.bnav_camera);
        setTxt('.bnav-sensors-label',  t.bnav_sensors);
        setTxt('.bnav-theme-label',    t.bnav_theme);
        setTxt('.bnav-settings-label', t.bnav_settings);
        setTxt('.bnav-logout-label',   t.bnav_logout);
        // Sensor drawer labels
        setTxt('.drawer-label-gas',      t.sensor_gas);
        setTxt('.drawer-label-temp',     t.sensor_temp);
        setTxt('.drawer-label-pressure', t.sensor_pressure);
        setTxt('.drawer-label-altitude', t.sensor_altitude);
        setTxt('.drawer-label-tilt',     t.sensor_tilt);
        // Joystick window
        setTxt('.joy-title-label',   t.joy_title);
        setTxt('.joy-forward-label', t.joy_forward);
        setTxt('.joy-back-label',    t.joy_back);
        setTxt('.joy-left-label',    t.joy_left);
        setTxt('.joy-right-label',   t.joy_right);
        setAllTxt('.joy-stop-label', t.joy_stop);
    }

    if (page === 'admin') {
        setTxt('.admin-page-title',   t.admin_title);
        setTxt('.admin-session-label', t.session_as);
        const rs = document.getElementById('rover-status');
        if (rs && ['A AGUARDAR...','AWAITING...','EN ESPERA...','EN ATTENTE...'].includes(rs.textContent.trim()))
            rs.textContent = t.admin_awaiting;
        setTxt('.stat-active-accounts', t.admin_active_accounts);
        setTxt('.stat-equipment',       t.admin_equipment);
        setTxt('.stat-infra',           t.admin_infra);
        setTxt('.stat-online-users',    t.admin_online_users);
        setTxt('.section-permissions',  t.admin_permissions);
        setTxt('.th-member',   t.admin_member);
        setTxt('.th-status',   t.admin_status);
        setTxt('.th-role',     t.admin_role);
        setTxt('.th-rover',    t.admin_rover_linked);
        setTxt('.th-action',   t.admin_action);
        setTxt('.section-rovers',       t.admin_rovers);
        setTxt('.stat-mqtt-total',      t.admin_mqtt_total);
        setTxt('.stat-logs-total',      t.admin_logs_total);
        setTxt('.stat-db-speed',        t.admin_db_speed);
        setTxt('.section-analytics',    t.admin_analytics);
        setTxt('.section-live-logs',    t.admin_live_logs);
        const regBtn = document.querySelector('.btn-register-rover');
        if (regBtn) regBtn.textContent = t.admin_register_rover;
    }

    if (page === 'logs') {
        setTxt('.logs-page-title',    t.logs_title);
        setTxt('.logs-session-label', t.session_as);
        setTxt('.stat-total-label',   t.logs_total);
        setTxt('.stat-page-label',    t.logs_page);
        setTxt('.stat-sensors-label', t.logs_sensors_avail);
        setTxt('.stat-update-label',  t.logs_last_update);
        setTxt('.filter-sensor-label',  t.logs_sensor_label);
        setTxt('.filter-start-label',   t.logs_start_label);
        setTxt('.filter-end-label',     t.logs_end_label);
        setTxt('.btn-clear-filters',    t.logs_clear);
        setTxt('.logs-table-title',     t.logs_table_title);
        setTxt('.th-alert',    t.logs_alert);
        setTxt('.th-timestamp',t.logs_timestamp);
        setTxt('.th-sensor',   t.logs_sensor_label);
        setTxt('.th-value',    t.logs_value);
        setTxt('.th-message',  t.logs_message);
        setTxt('.th-category', t.logs_category);
        // Update default option text
        const allSensors = document.querySelector('#filter-sensor option[value=""]');
        if (allSensors) allSensors.textContent = t.logs_all_sensors;
    }
}
