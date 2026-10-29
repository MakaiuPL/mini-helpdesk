PRAGMA foreign_keys = ON;

BEGIN;

CREATE TABLE users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL COLLATE NOCASE UNIQUE,
    password_hash TEXT    NOT NULL,
    full_name     TEXT    NOT NULL,
    role          TEXT    NOT NULL CHECK (role IN ('user', 'technician')),
    created_at    TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tickets (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT    NOT NULL CHECK (length(trim(title)) BETWEEN 3 AND 120),
    description TEXT    NOT NULL CHECK (length(trim(description)) BETWEEN 10 AND 5000),
    priority    TEXT    NOT NULL CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    status      TEXT    NOT NULL DEFAULT 'new'
                        CHECK (status IN ('new', 'in_progress', 'waiting', 'closed')),
    channel     TEXT    NOT NULL CHECK (channel IN ('phone', 'email', 'remote', 'form')),
    author_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    assignee_id INTEGER          REFERENCES users(id) ON DELETE SET NULL,
    created_at  TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    closed_at   TEXT,
    CHECK ((status = 'closed') = (closed_at IS NOT NULL))
);

CREATE TABLE comments (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id  INTEGER NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    author_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    body       TEXT    NOT NULL CHECK (length(trim(body)) BETWEEN 1 AND 2000),
    created_at TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE status_history (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id     INTEGER NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    changed_by_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    old_status    TEXT CHECK (old_status IS NULL OR old_status IN
                        ('new', 'in_progress', 'waiting', 'closed')),
    new_status    TEXT NOT NULL CHECK (new_status IN
                        ('new', 'in_progress', 'waiting', 'closed')),
    changed_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tickets_status        ON tickets(status);
CREATE INDEX idx_tickets_priority      ON tickets(priority);
CREATE INDEX idx_tickets_channel       ON tickets(channel);
CREATE INDEX idx_tickets_author        ON tickets(author_id);
CREATE INDEX idx_tickets_assignee      ON tickets(assignee_id);
CREATE INDEX idx_tickets_created       ON tickets(created_at DESC);
CREATE INDEX idx_comments_ticket       ON comments(ticket_id, created_at);
CREATE INDEX idx_status_history_ticket ON status_history(ticket_id, changed_at);

INSERT INTO users (id, username, password_hash, full_name, role, created_at) VALUES
(1, 'anna', 'scrypt:32768:8:1$T8PUDF85L6SmxrUi$9d116513fbf7caac66b2fad967644fbad38552c3f4d953ca2162cce705566ce36a4825b3c33914e083058642f46741a27ac6fd1834e9c90d9957c3f2a4231aec', 'Anna Kowalska', 'user', datetime('now', '-60 days')),
(2, 'piotr', 'scrypt:32768:8:1$3KNfMQtVta6gkrSY$57f308f67570844e4ee8e1cd861174dd30f97544975b9aedd566e9d7587b90f98de3238ccaf0d0028b1d320901d02ee5a69cacabb000be726368ca5068147f5f', 'Piotr Nowak', 'user', datetime('now', '-55 days')),
(3, 'marek', 'scrypt:32768:8:1$XTNDkatun3Lg0ypD$dcdd3fef12a2a122811f63e5ead3d1a5e347c3ae3a2dcf9b881d529c076a1c9e7ba48a7714d3304a8eb324f620a34466434a249798c9a8e27723ff405f60aec6', 'Marek Wiśniewski', 'technician', datetime('now', '-50 days')),
(4, 'ewa', 'scrypt:32768:8:1$0heBGTn67JEnAfwL$b7365ff9641fb96add3d9f67ad80e39b8d2a9ecca916a9894bed2b72db521bc2231808831dfc99c5dd48ff21c4f013514ba19f38fc858c69f059fe0816b18bbf', 'Ewa Zielińska', 'technician', datetime('now', '-45 days'));

INSERT INTO tickets (id, title, description, priority, status, channel, author_id, assignee_id, created_at, updated_at, closed_at) VALUES
(1, 'Nie działa drukarka w sali 204', 'Drukarka sieciowa nie odpowiada, mimo że jest włączona. Nie można wydrukować dokumentów.', 'high', 'in_progress', 'phone', 1, 3, datetime('now', '-12 days'), datetime('now', '-11 days'), NULL),
(2, 'Brak dostępu do folderu projektowego', 'Po zmianie komputera nie mam dostępu do folderu ProjektX na dysku sieciowym.', 'critical', 'closed', 'email', 1, 3, datetime('now', '-11 days'), datetime('now', '-10 days'), datetime('now', '-10 days')),
(3, 'Wolno działający laptop po aktualizacji', 'Laptop startuje kilka minut i zawiesza się przy otwieraniu przeglądarki.', 'medium', 'waiting', 'form', 2, 4, datetime('now', '-10 days'), datetime('now', '-8 days'), NULL),
(4, 'Nie mogę zalogować się do VPN', 'Klient VPN zwraca błąd uwierzytelniania od wczorajszego wieczoru.', 'high', 'new', 'form', 2, NULL, datetime('now', '-9 days'), datetime('now', '-9 days'), NULL),
(5, 'Prośba o instalację pakietu Office', 'Potrzebuję pakietu Office na nowym stanowisku pracy.', 'low', 'closed', 'phone', 1, 4, datetime('now', '-8 days'), datetime('now', '-7 days', '+6 hours'), datetime('now', '-7 days', '+6 hours')),
(6, 'Monitor miga przy podłączeniu stacji dokującej', 'Po podłączeniu stacji dokującej obraz miga co kilka sekund.', 'medium', 'in_progress', 'remote', 2, 3, datetime('now', '-7 days'), datetime('now', '-6 days'), NULL),
(7, 'Błąd 500 w aplikacji księgowej', 'Aplikacja księgowa zwraca błąd 500 przy zatwierdzaniu faktury.', 'critical', 'in_progress', 'email', 1, 4, datetime('now', '-6 days'), datetime('now', '-5 days'), NULL),
(8, 'Reset hasła do systemu kadrowego', 'Zapomniałem hasła do systemu kadrowego, proszę o reset.', 'low', 'closed', 'phone', 2, 3, datetime('now', '-5 days'), datetime('now', '-4 days', '+4 hours'), datetime('now', '-4 days', '+4 hours')),
(9, 'Brak miejsca na dysku sieciowym', 'Dysk sieciowy zgłasza brak miejsca przy próbie zapisu plików projektu.', 'high', 'waiting', 'email', 1, 3, datetime('now', '-4 days'), datetime('now', '-3 days'), NULL),
(10, 'Konfiguracja nowego telefonu służbowego', 'Nowy telefon służbowy wymaga konfiguracji poczty i profilu firmowego.', 'low', 'new', 'form', 2, NULL, datetime('now', '-3 days'), datetime('now', '-3 days'), NULL),
(11, 'Aplikacja CRM zawiesza się przy eksporcie', 'Eksport danych z CRM do Excela kończy się zawieszeniem aplikacji.', 'medium', 'in_progress', 'remote', 1, 4, datetime('now', '-2 days'), datetime('now', '-1 days'), NULL),
(12, 'Podejrzenie phishingu w wiadomości', 'Otrzymałem wiadomość z prośbą o podanie danych logowania. Wygląda podejrzanie.', 'critical', 'new', 'email', 2, NULL, datetime('now', '-1 days'), datetime('now', '-1 days'), NULL);

INSERT INTO comments (id, ticket_id, author_id, body, created_at) VALUES
(1, 1, 3, 'Sprawdzam konfigurację kolejki wydruków na serwerze.', datetime('now', '-11 days', '+1 hours')),
(2, 1, 3, 'Zamówiłem nowy toner, wymiana po dostawie.', datetime('now', '-11 days', '+3 hours')),
(3, 2, 3, 'Nadano uprawnienia do folderu i zweryfikowano dostęp.', datetime('now', '-10 days', '+1 hours')),
(4, 2, 3, 'Potwierdzone przez użytkownika, zgłoszenie można zamknąć.', datetime('now', '-10 days', '+2 hours')),
(5, 3, 4, 'Wykonano test dysku i sprawdzono logi systemowe.', datetime('now', '-9 days')),
(6, 3, 4, 'Czekam na informację, czy problem nadal występuje.', datetime('now', '-8 days')),
(7, 5, 4, 'Pakiet zainstalowany i aktywowany.', datetime('now', '-7 days', '+5 hours')),
(8, 6, 3, 'Zaktualizowałem sterowniki stacji dokującej.', datetime('now', '-6 days')),
(9, 7, 4, 'Błąd powtarza się na środowisku testowym, analizuję logi.', datetime('now', '-5 days')),
(10, 7, 4, 'Zgłoszenie przekazane do zespołu odpowiedzialnego za aplikację.', datetime('now', '-4 days')),
(11, 8, 3, 'Hasło zresetowane, dane wysłane bezpiecznym kanałem.', datetime('now', '-4 days', '+3 hours')),
(12, 9, 3, 'Uruchomiłem porządki na dysku i sprawdzam politykę retencji.', datetime('now', '-3 days')),
(13, 11, 4, 'Zbieram zrzuty pamięci aplikacji podczas eksportu.', datetime('now', '-1 days')),
(14, 11, 4, 'Problem prawdopodobnie dotyczy dużych plików powyżej 50 MB.', datetime('now', '-1 days', '+2 hours'));

INSERT INTO status_history (id, ticket_id, changed_by_id, old_status, new_status, changed_at) VALUES
(1, 1, 1, NULL, 'new', datetime('now', '-12 days')),
(2, 1, 3, 'new', 'in_progress', datetime('now', '-11 days')),
(3, 2, 1, NULL, 'new', datetime('now', '-11 days')),
(4, 2, 3, 'new', 'in_progress', datetime('now', '-11 days', '+2 hours')),
(5, 2, 3, 'in_progress', 'closed', datetime('now', '-10 days')),
(6, 3, 2, NULL, 'new', datetime('now', '-10 days')),
(7, 3, 4, 'new', 'in_progress', datetime('now', '-9 days')),
(8, 3, 4, 'in_progress', 'waiting', datetime('now', '-8 days')),
(9, 4, 2, NULL, 'new', datetime('now', '-9 days')),
(10, 5, 1, NULL, 'new', datetime('now', '-8 days')),
(11, 5, 4, 'new', 'in_progress', datetime('now', '-8 days', '+3 hours')),
(12, 5, 4, 'in_progress', 'closed', datetime('now', '-7 days', '+6 hours')),
(13, 6, 2, NULL, 'new', datetime('now', '-7 days')),
(14, 6, 3, 'new', 'in_progress', datetime('now', '-6 days')),
(15, 7, 1, NULL, 'new', datetime('now', '-6 days')),
(16, 7, 4, 'new', 'in_progress', datetime('now', '-5 days')),
(17, 8, 2, NULL, 'new', datetime('now', '-5 days')),
(18, 8, 3, 'new', 'in_progress', datetime('now', '-5 days', '+2 hours')),
(19, 8, 3, 'in_progress', 'closed', datetime('now', '-4 days', '+4 hours')),
(20, 9, 1, NULL, 'new', datetime('now', '-4 days')),
(21, 9, 3, 'new', 'in_progress', datetime('now', '-3 days')),
(22, 9, 3, 'in_progress', 'waiting', datetime('now', '-3 days', '+1 hours')),
(23, 10, 2, NULL, 'new', datetime('now', '-3 days')),
(24, 11, 1, NULL, 'new', datetime('now', '-2 days')),
(25, 11, 4, 'new', 'in_progress', datetime('now', '-1 days')),
(26, 12, 2, NULL, 'new', datetime('now', '-1 days'));

COMMIT;
