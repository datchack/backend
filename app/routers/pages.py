import ast
import json
import re
from functools import lru_cache
from html import escape
from pathlib import Path

from bs4 import BeautifulSoup
from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse, Response as FastAPIResponse

from app.config import (
    APP_BASE_URL,
    LEGAL_BUSINESS_ADDRESS,
    LEGAL_BUSINESS_ID,
    LEGAL_BUSINESS_NAME,
    LEGAL_BUSINESS_STATUS,
    LEGAL_CONTACT_EMAIL,
    LEGAL_HOSTING_PROVIDER,
    LEGAL_MEDIATOR_ADDRESS,
    LEGAL_MEDIATOR_NAME,
    LEGAL_MEDIATOR_URL,
    LEGAL_PUBLISHER_NAME,
    LEGAL_VAT_ID,
)
from app.services.accounts import get_db_connection, require_owner, utc_now
from app.services.pulse import build_public_market_pulse

router = APIRouter()


SUPPORTED_LOCALES = {
    "fr": {"prefix": "", "hreflang": "fr", "name": "Français", "flag": "🇫🇷", "dir": "ltr"},
    "en": {"prefix": "/en", "hreflang": "en", "name": "English", "flag": "🇬🇧", "dir": "ltr"},
    "es": {"prefix": "/es", "hreflang": "es", "name": "Español", "flag": "🇪🇸", "dir": "ltr"},
    "pt-br": {"prefix": "/pt-br", "hreflang": "pt-BR", "name": "Português BR", "flag": "🇧🇷", "dir": "ltr"},
    "de": {"prefix": "/de", "hreflang": "de", "name": "Deutsch", "flag": "🇩🇪", "dir": "ltr"},
    "ar": {"prefix": "/ar", "hreflang": "ar", "name": "العربية", "flag": "🇸🇦", "dir": "rtl"},
    "ja": {"prefix": "/ja", "hreflang": "ja", "name": "日本語", "flag": "🇯🇵", "dir": "ltr"},
    "hi": {"prefix": "/hi", "hreflang": "hi", "name": "हिन्दी", "flag": "🇮🇳", "dir": "ltr"},
    "id": {"prefix": "/id", "hreflang": "id", "name": "Bahasa Indonesia", "flag": "🇮🇩", "dir": "ltr"},
    "zh": {"prefix": "/zh", "hreflang": "zh-Hans", "name": "简体中文", "flag": "🇨🇳", "dir": "ltr"},
}

LOCALE_PREFIXES = {cfg["prefix"].strip("/"): code for code, cfg in SUPPORTED_LOCALES.items() if cfg["prefix"]}

LOCALE_COPY = {
    "en": {
        "meta_title": "XAUTERMINAL - Professional macro and trading terminal",
        "meta_description": "XAUTERMINAL centralizes charting, economic calendar, multi-source news, macro alerts and market profiles in a professional terminal for traders.",
        "terms_description": "XAUTERMINAL terms covering service access, subscriptions, payment, immediate digital access and responsibilities.",
        "privacy_description": "XAUTERMINAL privacy policy covering account data, sessions, payments and service providers.",
        "risk_description": "Trading risk warning covering market data, financial instruments and the use of XAUTERMINAL tools.",
        "hero_copy": "A macro workstation to track news, the economic calendar, market drivers and your charts in a fast, customizable, decision-focused interface.",
        "hero_trial": "Start 7-day trial",
        "hero_login": "I already have an account",
        "nav_tools": "Tools",
        "nav_markets": "Markets",
        "nav_pricing": "Plans",
        "nav_login": "Login",
        "nav_terminal": "Open terminal",
        "nav_account": "My account",
        "nav_support": "Support",
        "features_title": "Everything that matters before a market decision.",
        "pricing_title": "Try the terminal, then choose the rhythm that fits you.",
        "pricing_monthly_label": "Monthly",
        "pricing_yearly_label": "Yearly",
        "pricing_lifetime_label": "Lifetime",
        "pricing_choose": "Choose this plan",
        "pricing_note_title": "Secure trial and payment",
        "footer_trial": "Start trial",
        "footer_tagline": "Professional macro and trading terminal. Information tool, not financial advice.",
        "billing_redirect": "Redirecting to payment...",
    },
    "es": {
        "meta_title": "XAUTERMINAL - Terminal macro y trading profesional",
        "meta_description": "XAUTERMINAL centraliza gráficos, calendario económico, noticias multi-fuente, alertas macro y perfiles de mercado en un terminal profesional para traders.",
        "terms_description": "Condiciones de XAUTERMINAL sobre acceso al servicio, suscripciones, pago, acceso digital inmediato y responsabilidades.",
        "privacy_description": "Política de privacidad de XAUTERMINAL sobre datos de cuenta, sesiones, pagos y proveedores.",
        "risk_description": "Advertencia de riesgos de trading sobre datos de mercado, instrumentos financieros y uso de las herramientas XAUTERMINAL.",
        "hero_copy": "Un puesto de trabajo macro para seguir noticias, calendario económico, drivers de mercado y gráficos en una interfaz rápida, personalizable y orientada a la decisión.",
        "hero_trial": "Iniciar prueba de 7 días",
        "hero_login": "Ya tengo una cuenta",
        "nav_tools": "Herramientas",
        "nav_markets": "Mercados",
        "nav_pricing": "Planes",
        "nav_login": "Conexión",
        "nav_terminal": "Abrir terminal",
        "nav_account": "Mi cuenta",
        "nav_support": "Soporte",
        "features_title": "Todo lo importante antes de una decisión de mercado.",
        "pricing_title": "Prueba el terminal y elige el ritmo que encaje contigo.",
        "pricing_monthly_label": "Mensual",
        "pricing_yearly_label": "Anual",
        "pricing_lifetime_label": "Lifetime",
        "pricing_choose": "Elegir este plan",
        "pricing_note_title": "Prueba y pago seguro",
        "footer_trial": "Iniciar prueba",
        "footer_tagline": "Terminal macro y trading profesional. Herramienta informativa, no asesoramiento financiero.",
        "billing_redirect": "Redirección al pago...",
    },
    "pt-br": {
        "meta_title": "XAUTERMINAL - Terminal macro e trading profissional",
        "meta_description": "XAUTERMINAL centraliza gráficos, calendário econômico, notícias multi-fonte, alertas macro e perfis de mercado em um terminal profissional para traders.",
        "terms_description": "Termos da XAUTERMINAL sobre acesso ao serviço, assinaturas, pagamento, acesso digital imediato e responsabilidades.",
        "privacy_description": "Política de privacidade da XAUTERMINAL sobre dados de conta, sessões, pagamentos e prestadores.",
        "risk_description": "Aviso de risco de trading sobre dados de mercado, instrumentos financeiros e uso das ferramentas XAUTERMINAL.",
        "hero_copy": "Uma estação macro para acompanhar notícias, calendário econômico, drivers de mercado e gráficos em uma interface rápida, personalizável e orientada à decisão.",
        "hero_trial": "Iniciar teste de 7 dias",
        "hero_login": "Já tenho uma conta",
        "nav_tools": "Ferramentas",
        "nav_markets": "Mercados",
        "nav_pricing": "Planos",
        "nav_login": "Entrar",
        "nav_terminal": "Abrir terminal",
        "nav_account": "Minha conta",
        "nav_support": "Suporte",
        "features_title": "Tudo que importa antes de uma decisão de mercado.",
        "pricing_title": "Teste o terminal e escolha o ritmo ideal.",
        "pricing_monthly_label": "Mensal",
        "pricing_yearly_label": "Anual",
        "pricing_lifetime_label": "Lifetime",
        "pricing_choose": "Escolher este plano",
        "pricing_note_title": "Teste e pagamento seguro",
        "footer_trial": "Iniciar teste",
        "footer_tagline": "Terminal macro e trading profissional. Ferramenta informativa, não aconselhamento financeiro.",
        "billing_redirect": "Redirecionando para o pagamento...",
    },
    "de": {
        "meta_title": "XAUTERMINAL - Professionelles Makro- und Trading-Terminal",
        "meta_description": "XAUTERMINAL bündelt Charting, Wirtschaftskalender, Multi-Source-News, Makro-Warnungen und Marktprofile in einem professionellen Terminal für Trader.",
        "terms_description": "XAUTERMINAL Bedingungen zu Servicezugang, Abonnements, Zahlung, sofortigem digitalem Zugang und Verantwortlichkeiten.",
        "privacy_description": "XAUTERMINAL Datenschutzerklärung zu Kontodaten, Sitzungen, Zahlungen und Dienstleistern.",
        "risk_description": "Trading-Risikohinweis zu Marktdaten, Finanzinstrumenten und der Nutzung der XAUTERMINAL Tools.",
        "hero_copy": "Ein Makro-Arbeitsplatz für News, Wirtschaftskalender, Markttreiber und Charts in einer schnellen, anpassbaren und entscheidungsorientierten Oberfläche.",
        "hero_trial": "7-Tage-Test starten",
        "hero_login": "Ich habe bereits ein Konto",
        "nav_tools": "Tools",
        "nav_markets": "Märkte",
        "nav_pricing": "Tarife",
        "nav_login": "Login",
        "nav_terminal": "Terminal öffnen",
        "nav_account": "Mein Konto",
        "nav_support": "Support",
        "features_title": "Alles Wichtige vor einer Marktentscheidung.",
        "pricing_title": "Teste das Terminal und wähle deinen Rhythmus.",
        "pricing_monthly_label": "Monatlich",
        "pricing_yearly_label": "Jährlich",
        "pricing_lifetime_label": "Lifetime",
        "pricing_choose": "Diesen Tarif wählen",
        "pricing_note_title": "Sichere Testphase und Zahlung",
        "footer_trial": "Test starten",
        "footer_tagline": "Professionelles Makro- und Trading-Terminal. Informationstool, keine Finanzberatung.",
        "billing_redirect": "Weiterleitung zur Zahlung...",
    },
    "ar": {
        "meta_title": "XAUTERMINAL - منصة ماكرو وتداول احترافية",
        "meta_description": "يجمع XAUTERMINAL الرسوم البيانية والتقويم الاقتصادي والأخبار متعددة المصادر والتنبيهات الكلية وملفات الأسواق في منصة احترافية للمتداولين.",
        "terms_description": "شروط XAUTERMINAL حول الوصول إلى الخدمة والاشتراكات والدفع والوصول الرقمي الفوري والمسؤوليات.",
        "privacy_description": "سياسة خصوصية XAUTERMINAL حول بيانات الحساب والجلسات والمدفوعات ومقدمي الخدمات.",
        "risk_description": "تحذير مخاطر التداول حول بيانات السوق والأدوات المالية واستخدام أدوات XAUTERMINAL.",
        "hero_copy": "مساحة عمل ماكرو لمتابعة الأخبار والتقويم الاقتصادي ومحركات السوق والرسوم البيانية عبر واجهة سريعة وقابلة للتخصيص وموجهة للقرار.",
        "hero_trial": "ابدأ تجربة 7 أيام",
        "hero_login": "لدي حساب بالفعل",
        "nav_tools": "الأدوات",
        "nav_markets": "الأسواق",
        "nav_pricing": "الخطط",
        "nav_login": "تسجيل الدخول",
        "nav_terminal": "فتح المنصة",
        "nav_account": "حسابي",
        "nav_support": "الدعم",
        "features_title": "كل ما يهم قبل اتخاذ قرار في السوق.",
        "pricing_title": "جرّب المنصة ثم اختر الخطة المناسبة لك.",
        "pricing_monthly_label": "شهري",
        "pricing_yearly_label": "سنوي",
        "pricing_lifetime_label": "مدى الحياة",
        "pricing_choose": "اختر هذه الخطة",
        "pricing_note_title": "تجربة ودفع آمن",
        "footer_trial": "ابدأ التجربة",
        "footer_tagline": "منصة ماكرو وتداول احترافية. أداة معلومات وليست نصيحة مالية.",
        "billing_redirect": "جارٍ التحويل إلى الدفع...",
    },
    "ja": {
        "meta_title": "XAUTERMINAL - プロ向けマクロ・トレーディング端末",
        "meta_description": "XAUTERMINAL は、チャート、経済カレンダー、複数ソースのニュース、マクロアラート、市場プロファイルをプロ向け端末に集約します。",
        "terms_description": "サービスアクセス、サブスクリプション、支払い、即時デジタルアクセス、責任に関する XAUTERMINAL の利用規約。",
        "privacy_description": "アカウントデータ、セッション、支払い、サービス提供者に関する XAUTERMINAL のプライバシーポリシー。",
        "risk_description": "市場データ、金融商品、XAUTERMINAL ツールの利用に関する取引リスク警告。",
        "hero_copy": "ニュース、経済カレンダー、市場ドライバー、チャートを素早くカスタマイズ可能な意思決定向けインターフェースで確認できるマクロワークステーション。",
        "hero_trial": "7日間トライアルを開始",
        "hero_login": "すでにアカウントを持っています",
        "nav_tools": "ツール",
        "nav_markets": "市場",
        "nav_pricing": "プラン",
        "nav_login": "ログイン",
        "nav_terminal": "端末を開く",
        "nav_account": "アカウント",
        "nav_support": "サポート",
        "features_title": "市場判断の前に必要な情報を一か所に。",
        "pricing_title": "端末を試して、自分に合うプランを選択。",
        "pricing_monthly_label": "月額",
        "pricing_yearly_label": "年額",
        "pricing_lifetime_label": "Lifetime",
        "pricing_choose": "このプランを選ぶ",
        "pricing_note_title": "安全なトライアルと決済",
        "footer_trial": "トライアル開始",
        "footer_tagline": "プロ向けマクロ・トレーディング端末。情報ツールであり、金融助言ではありません。",
        "billing_redirect": "決済へ移動しています...",
    },
    "hi": {
        "meta_title": "XAUTERMINAL - प्रोफेशनल मैक्रो और ट्रेडिंग टर्मिनल",
        "meta_description": "XAUTERMINAL चार्टिंग, आर्थिक कैलेंडर, मल्टी-सोर्स समाचार, मैक्रो अलर्ट और मार्केट प्रोफाइल को ट्रेडर्स के लिए एक प्रोफेशनल टर्मिनल में जोड़ता है.",
        "terms_description": "सेवा पहुंच, सब्सक्रिप्शन, भुगतान, तत्काल डिजिटल पहुंच और जिम्मेदारियों से जुड़े XAUTERMINAL नियम.",
        "privacy_description": "खाता डेटा, सेशन, भुगतान और सेवा प्रदाताओं से जुड़ी XAUTERMINAL गोपनीयता नीति.",
        "risk_description": "मार्केट डेटा, वित्तीय इंस्ट्रूमेंट और XAUTERMINAL टूल्स के उपयोग से जुड़े ट्रेडिंग जोखिम की चेतावनी.",
        "hero_copy": "समाचार, आर्थिक कैलेंडर, मार्केट ड्राइवर और चार्ट को तेज, कस्टमाइजेबल और निर्णय-केंद्रित इंटरफेस में ट्रैक करने वाला मैक्रो वर्कस्टेशन.",
        "hero_trial": "7 दिन का ट्रायल शुरू करें",
        "hero_login": "मेरे पास पहले से खाता है",
        "nav_tools": "टूल्स",
        "nav_markets": "मार्केट्स",
        "nav_pricing": "प्लान",
        "nav_login": "लॉगिन",
        "nav_terminal": "टर्मिनल खोलें",
        "nav_account": "मेरा खाता",
        "nav_support": "सहायता",
        "features_title": "मार्केट निर्णय से पहले जरूरी सब कुछ.",
        "pricing_title": "टर्मिनल आज़माएँ और अपना प्लान चुनें.",
        "pricing_monthly_label": "मासिक",
        "pricing_yearly_label": "वार्षिक",
        "pricing_lifetime_label": "Lifetime",
        "pricing_choose": "यह प्लान चुनें",
        "pricing_note_title": "सुरक्षित ट्रायल और भुगतान",
        "footer_trial": "ट्रायल शुरू करें",
        "footer_tagline": "प्रोफेशनल मैक्रो और ट्रेडिंग टर्मिनल. सूचना उपकरण, वित्तीय सलाह नहीं.",
        "billing_redirect": "भुगतान पर भेजा जा रहा है...",
    },
    "id": {
        "meta_title": "XAUTERMINAL - Terminal makro dan trading profesional",
        "meta_description": "XAUTERMINAL memusatkan charting, kalender ekonomi, berita multi-sumber, alert makro, dan profil pasar dalam terminal profesional untuk trader.",
        "terms_description": "Ketentuan XAUTERMINAL tentang akses layanan, langganan, pembayaran, akses digital langsung, dan tanggung jawab.",
        "privacy_description": "Kebijakan privasi XAUTERMINAL tentang data akun, sesi, pembayaran, dan penyedia layanan.",
        "risk_description": "Peringatan risiko trading tentang data pasar, instrumen keuangan, dan penggunaan alat XAUTERMINAL.",
        "hero_copy": "Workspace makro untuk mengikuti berita, kalender ekonomi, driver pasar, dan chart dalam antarmuka cepat, personal, dan berorientasi keputusan.",
        "hero_trial": "Mulai uji coba 7 hari",
        "hero_login": "Saya sudah punya akun",
        "nav_tools": "Alat",
        "nav_markets": "Pasar",
        "nav_pricing": "Paket",
        "nav_login": "Masuk",
        "nav_terminal": "Buka terminal",
        "nav_account": "Akun saya",
        "nav_support": "Dukungan",
        "features_title": "Semua yang penting sebelum keputusan pasar.",
        "pricing_title": "Coba terminal, lalu pilih ritme yang cocok.",
        "pricing_monthly_label": "Bulanan",
        "pricing_yearly_label": "Tahunan",
        "pricing_lifetime_label": "Lifetime",
        "pricing_choose": "Pilih paket ini",
        "pricing_note_title": "Uji coba dan pembayaran aman",
        "footer_trial": "Mulai uji coba",
        "footer_tagline": "Terminal makro dan trading profesional. Alat informasi, bukan nasihat keuangan.",
        "billing_redirect": "Mengalihkan ke pembayaran...",
    },
    "zh": {
        "meta_title": "XAUTERMINAL - 专业宏观与交易终端",
        "meta_description": "XAUTERMINAL 将图表、经济日历、多源新闻、宏观提醒和市场档案集中在一个面向交易者的专业终端中。",
        "terms_description": "XAUTERMINAL 关于服务访问、订阅、付款、即时数字访问和责任的条款。",
        "privacy_description": "XAUTERMINAL 关于账户数据、会话、付款和服务提供商的隐私政策。",
        "risk_description": "关于市场数据、金融工具以及使用 XAUTERMINAL 工具的交易风险提示。",
        "hero_copy": "一个宏观工作台，用快速、可定制、面向决策的界面跟踪新闻、经济日历、市场驱动因素和图表。",
        "hero_trial": "开始 7 天试用",
        "hero_login": "我已有账户",
        "nav_tools": "工具",
        "nav_markets": "市场",
        "nav_pricing": "方案",
        "nav_login": "登录",
        "nav_terminal": "打开终端",
        "nav_account": "我的账户",
        "nav_support": "支持",
        "features_title": "市场决策前需要关注的一切。",
        "pricing_title": "先试用终端，再选择适合你的方案。",
        "pricing_monthly_label": "月付",
        "pricing_yearly_label": "年付",
        "pricing_lifetime_label": "Lifetime",
        "pricing_choose": "选择此方案",
        "pricing_note_title": "安全试用与支付",
        "footer_trial": "开始试用",
        "footer_tagline": "专业宏观与交易终端。信息工具，不构成金融建议。",
        "billing_redirect": "正在跳转到支付...",
    },
}


def extract_static_locale_copy(locale: str = "en") -> dict[str, str]:
    try:
        with open("static/landing.js", "r", encoding="utf-8") as handle:
            source = handle.read()
    except OSError:
        return {}

    result: dict[str, str] = {}
    for object_name in ("LANDING_COPY", "SEO_COPY"):
        object_start = source.find(f"const {object_name} = {{")
        if object_start < 0:
            continue
        locale_marker = f"\n    {locale}: {{"
        locale_start = source.find(locale_marker, object_start)
        if locale_start < 0:
            continue
        brace_start = source.find("{", locale_start + 1)
        if brace_start < 0:
            continue
        depth = 0
        quote: str | None = None
        escaped = False
        block_end = brace_start
        for index, char in enumerate(source[brace_start:], start=brace_start):
            if quote:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == quote:
                    quote = None
                continue
            if char in {"'", '"'}:
                quote = char
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    block_end = index
                    break
        block = source[brace_start + 1:block_end]
        for match in re.finditer(r"\n\s*([A-Za-z0-9_]+):\s*('(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\")", block):
            try:
                result[match.group(1)] = ast.literal_eval(match.group(2))
            except (SyntaxError, ValueError):
                continue
    return result


STATIC_EN_COPY = extract_static_locale_copy("en")
TRANSLATION_DIR = Path(__file__).resolve().parents[1] / "translations"


@lru_cache(maxsize=32)
def load_locale_file(locale: str) -> dict[str, str]:
    path = TRANSLATION_DIR / f"{locale}.json"
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return {}
    return {str(key): str(value) for key, value in data.items() if isinstance(value, str)}


@lru_cache(maxsize=512)
def load_market_locale_file(locale: str, path: str) -> dict[str, str]:
    file_path = TRANSLATION_DIR / f"market-{locale}.json"
    try:
        with file_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return {}
    page_data = data.get(path, {})
    return {str(key): str(value) for key, value in page_data.items() if isinstance(value, str)}


def absolute_url(path: str = "/") -> str:
    suffix = path if path.startswith("/") else f"/{path}"
    return f"{APP_BASE_URL}{suffix}"


def locale_path(path: str, locale: str = "fr") -> str:
    clean_path = path if path.startswith("/") else f"/{path}"
    if clean_path != "/" and clean_path.endswith("/"):
        clean_path = clean_path.rstrip("/")
    prefix = SUPPORTED_LOCALES.get(locale, SUPPORTED_LOCALES["fr"])["prefix"]
    if not prefix:
        return clean_path
    return prefix if clean_path == "/" else f"{prefix}{clean_path}"


def alternate_links(path: str) -> str:
    links = [
        f'    <link rel="alternate" hreflang="{cfg["hreflang"]}" href="{absolute_url(locale_path(path, locale))}">'
        for locale, cfg in SUPPORTED_LOCALES.items()
    ]
    links.append(f'    <link rel="alternate" hreflang="x-default" href="{absolute_url(locale_path(path, "en"))}">')
    return "\n".join(links)


def language_selector(current_locale: str, path: str) -> str:
    current = SUPPORTED_LOCALES.get(current_locale, SUPPORTED_LOCALES["fr"])
    options = "\n".join(
        f"""        <a class="language-option{' active' if locale == current_locale else ''}" href="{escape(locale_path(path, locale), quote=True)}" data-lang-option="{locale}" hreflang="{cfg['hreflang']}" lang="{cfg['hreflang']}">
            <span class="language-flag" aria-hidden="true">{cfg['flag']}</span>
            <span>{escape(cfg['name'])}</span>
            <strong>{locale.upper()}</strong>
        </a>"""
        for locale, cfg in SUPPORTED_LOCALES.items()
    )
    return f"""<div class="language-picker" data-language-picker>
    <button type="button" class="landing-lang language-trigger" data-lang-toggle aria-haspopup="true" aria-expanded="false" aria-label="Choisir la langue">
        <span class="language-flag" aria-hidden="true">{current['flag']}</span>
        <span class="language-code">{current_locale.upper()}</span>
    </button>
    <div class="language-menu" data-language-menu role="menu">
{options}
    </div>
</div>"""


def localized_copy(locale: str) -> dict[str, str]:
    if locale == "fr":
        return {}
    copy = {**STATIC_EN_COPY, **load_locale_file(locale), **LOCALE_COPY.get("en", {}), **LOCALE_COPY.get(locale, {})}
    copy.setdefault("meta_description", copy.get("hero_copy", ""))
    return copy


def localize_structured_data(
    payload,
    locale_hreflang: str,
    canonical_url: str,
    page_title: str = "",
    page_description: str = "",
    headline: str = "",
    faq_pairs=None,
):
    if isinstance(payload, list):
        return [
            localize_structured_data(
                item,
                locale_hreflang,
                canonical_url,
                page_title,
                page_description,
                headline,
                faq_pairs,
            )
            for item in payload
        ]
    if not isinstance(payload, dict):
        return payload

    updated = {
        key: localize_structured_data(
            value,
            locale_hreflang,
            canonical_url,
            page_title,
            page_description,
            headline,
            faq_pairs,
        )
        for key, value in payload.items()
    }
    if "inLanguage" in updated:
        updated["inLanguage"] = locale_hreflang

    json_type = updated.get("@type")
    if isinstance(json_type, list):
        types = set(json_type)
    else:
        types = {json_type}
    if types.intersection({"WebPage", "Article", "FAQPage"}):
        updated["url"] = canonical_url
    if "Article" in types:
        if headline:
            updated["headline"] = headline
        if page_description:
            updated["description"] = page_description
        updated["mainEntityOfPage"] = canonical_url
    if "WebPage" in types:
        if page_title:
            updated["name"] = page_title
        if page_description:
            updated["description"] = page_description
    if "SoftwareApplication" in types and page_description:
        updated["description"] = page_description
        for offer in updated.get("offers", []):
            if not isinstance(offer, dict):
                continue
            if offer.get("price") == "29":
                offer["name"] = "Monthly"
            elif offer.get("price") == "249":
                offer["name"] = "Yearly"
            elif offer.get("price") == "599":
                offer["name"] = "Lifetime"
    if "FAQPage" in types and faq_pairs:
        updated["mainEntity"] = [
            {
                "@type": "Question",
                "name": question,
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": answer,
                },
            }
            for question, answer in faq_pairs
        ]
    return updated


def localize_html(html: str, locale: str, path: str) -> str:
    if locale not in SUPPORTED_LOCALES:
        locale = "fr"
    soup = BeautifulSoup(html, "html.parser")
    locale_cfg = SUPPORTED_LOCALES[locale]
    if soup.html:
        soup.html["lang"] = locale_cfg["hreflang"]
        soup.html["dir"] = locale_cfg["dir"]

    canonical_url = absolute_url(locale_path(path, locale))
    canonical = soup.find("link", rel="canonical")
    if canonical:
        canonical["href"] = canonical_url
        canonical.insert_after(BeautifulSoup("\n" + alternate_links(path), "html.parser"))

    for tag in soup.find_all("meta", property="og:url"):
        tag["content"] = canonical_url

    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        if not script.string:
            continue
        try:
            payload = json.loads(script.string)
        except json.JSONDecodeError:
            continue
        script.string = json.dumps(
            localize_structured_data(payload, locale_cfg["hreflang"], canonical_url),
            ensure_ascii=False,
        )

    for stylesheet in soup.find_all("link", rel="stylesheet"):
        href = stylesheet.get("href", "")
        if href.startswith("/static/styles.css"):
            stylesheet["href"] = "/static/css/landing.css?v=20260519-perf"

    for script_tag in soup.find_all("script", src=True):
        if script_tag["src"].startswith("/static/landing.js"):
            script_tag["src"] = "/static/landing.js?v=20260520-seo-meta"

    copy = localized_copy(locale)
    if copy:
        for element in soup.find_all(attrs={"data-i18n": True}):
            value = copy.get(element["data-i18n"])
            if value:
                element.string = value
        for element in soup.find_all(attrs={"data-i18n-content": True}):
            value = copy.get(element["data-i18n-content"])
            if value:
                element["content"] = value
        title = soup.find("title")
        if title and copy.get(title.get("data-i18n", "")):
            title.string = copy[title["data-i18n"]]

    market_copy = load_market_locale_file(locale, path)
    if market_copy:
        for element in soup.find_all(attrs={"data-market-i18n": True}):
            value = market_copy.get(element["data-market-i18n"])
            if value:
                element.string = value
        for element in soup.find_all(attrs={"data-market-content": True}):
            value = market_copy.get(element["data-market-content"])
            if value:
                element["content"] = value
        title = soup.find("title", attrs={"data-market-i18n": True})
        if title and market_copy.get(title["data-market-i18n"]):
            title.string = market_copy[title["data-market-i18n"]]
        for script in soup.find_all("script"):
            if script.string and "window.XT_MARKET_COPY" in script.string:
                match = re.search(r"window\\.XT_MARKET_COPY\\s*=\\s*(.*);", script.string, re.S)
                if match:
                    try:
                        market_payload = json.loads(match.group(1))
                        market_payload[locale] = market_copy
                        script.string = f"window.XT_MARKET_COPY = {json.dumps(market_payload, ensure_ascii=False)};"
                    except json.JSONDecodeError:
                        pass

    page_title = soup.title.get_text(strip=True) if soup.title else ""
    description_tag = soup.find("meta", attrs={"name": "description"})
    page_description = description_tag.get("content", "") if description_tag else ""
    h1 = soup.find("h1")
    page_headline = h1.get_text(" ", strip=True) if h1 else page_title
    faq_pairs = [
        (article.find("h3").get_text(" ", strip=True), article.find("p").get_text(" ", strip=True))
        for article in soup.select(".faq-card, .faq-grid article, .resource-faq article")
        if article.find("h3") and article.find("p")
    ]
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        if not script.string:
            continue
        try:
            payload = json.loads(script.string)
        except json.JSONDecodeError:
            continue
        script.string = json.dumps(
            localize_structured_data(
                payload,
                locale_cfg["hreflang"],
                canonical_url,
                page_title,
                page_description,
                page_headline,
                faq_pairs,
            ),
            ensure_ascii=False,
        )

    initial_script = soup.new_tag("script")
    initial_script.string = (
        f"window.XT_INITIAL_LANG={json.dumps(locale)};"
        f"window.XT_SUPPORTED_LANGS={json.dumps(list(SUPPORTED_LOCALES))};"
        f"window.XT_LANGUAGE_META={json.dumps(SUPPORTED_LOCALES, ensure_ascii=False)};"
        f"window.XT_LOCALE_COPY={json.dumps(copy, ensure_ascii=False)};"
    )
    if soup.head:
        soup.head.append(initial_script)
    for button in soup.select("[data-lang-toggle]"):
        wrapper = BeautifulSoup(language_selector(locale, path), "html.parser")
        button.replace_with(wrapper)
    return str(soup)


@lru_cache(maxsize=32)
def localized_landing(locale: str = "fr") -> str:
    with open("templates/landing.html", "r", encoding="utf-8") as handle:
        return localize_html(handle.read(), locale, "/")


FAVICON_LINKS = """    <link rel="icon" href="/favicon.ico" sizes="any">
    <link rel="icon" type="image/png" sizes="48x48" href="/static/favicon-48x48.png">
    <link rel="icon" type="image/png" sizes="32x32" href="/static/favicon-32x32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="/static/favicon-16x16.png">
    <link rel="apple-touch-icon" href="/static/apple-icon-180x180.png">
    <link rel="manifest" href="/static/manifest.json">"""

BRAND_MARKUP = """<img class="brand-logo" src="/static/xauterminal-logo.png" alt="" width="36" height="36">
            <span>XAUTERMINAL</span>"""

PUBLIC_FOOTER = """    <footer class="landing-footer">
        <div class="footer-brand">
            <a class="landing-brand" href="/" aria-label="XAUTERMINAL">
                <img class="brand-logo" src="/static/xauterminal-logo.png" alt="" width="36" height="36">
                <span>XAUTERMINAL</span>
            </a>
            <p data-i18n="footer_tagline">Terminal macro et trading professionnel. Outil d'information, pas un conseil financier.</p>
            <a class="resource-cta" href="/#pricing" data-i18n="footer_trial">Démarrer l'essai</a>
        </div>
        <nav class="footer-grid" aria-label="Plan du site">
            <div class="footer-column">
                <h3 data-i18n="footer_product">Produit</h3>
                <a href="/#features" data-i18n="nav_tools">Outils</a>
                <a href="/marches" data-i18n="nav_markets">Marchés</a>
                <a href="/market-pulse" data-i18n="nav_pulse">Market Pulse</a>
                <a href="/#pricing" data-i18n="nav_pricing">Formules</a>
                <a href="/terminal" data-i18n="nav_terminal">Ouvrir le terminal</a>
            </div>
            <div class="footer-column">
                <h3 data-i18n="footer_learn">Apprendre</h3>
                <a href="/guides" data-i18n="nav_guides">Guides</a>
                <a href="/ressources" data-i18n="nav_resources">Ressources</a>
                <a href="/terminal-xauusd" data-i18n="resource_terminal_short">XAU/USD</a>
                <a href="/guide/trading-or-macro" data-i18n="resource_guide_short">Guide macro</a>
            </div>
            <div class="footer-column">
                <h3 data-i18n="footer_markets">Marchés et données</h3>
                <a href="/marches" data-i18n="nav_markets">Marchés</a>
                <a href="/calendrier-economique-or" data-i18n="resource_calendar_short">Calendrier or</a>
                <a href="/news-forex-or" data-i18n="resource_news_short">News forex</a>
                <a href="/market-pulse" data-i18n="nav_pulse">Market Pulse</a>
                <a href="/guides/dxy-taux-us-or" data-i18n="footer_dxy_rates">DXY et taux US</a>
                <a href="/guides/bias-desk-trading" data-i18n="footer_bias_desk">Bias Desk</a>
            </div>
            <div class="footer-column">
                <h3 data-i18n="footer_account">Compte</h3>
                <a href="/account" data-i18n="nav_account">Mon compte</a>
                <a href="/support" data-i18n="nav_support">Support</a>
                <a href="/#pricing" data-i18n="footer_subscriptions">Abonnements</a>
                <a href="mailto:mdtrading@xauterminal.com" data-i18n="footer_contact">Contact</a>
            </div>
            <div class="footer-column">
                <h3 data-i18n="footer_legal">Légal</h3>
                <a href="/terms" data-i18n="terms_kicker">CGU</a>
                <a href="/privacy" data-i18n="privacy_kicker">Confidentialité</a>
                <a href="/risk-disclaimer" data-i18n="risk_footer_link">Disclaimer trading</a>
            </div>
        </nav>
        <div class="footer-risk" data-i18n="footer_risk">
            Le trading comporte un risque de perte. XAUTERMINAL fournit des informations de marché et des outils d'organisation, sans conseil financier personnalisé.
        </div>
    </footer>"""

LEGAL_PAGE_META = {
    "terms_title": {
        "title": "Conditions générales d'utilisation",
        "kicker": "CGU",
        "description": "Conditions générales d'utilisation de XAUTERMINAL, accès au service, abonnements, paiement et responsabilités.",
    },
    "privacy_title": {
        "title": "Politique de confidentialité",
        "kicker": "CONFIDENTIALITÉ",
        "description": "Politique de confidentialité de XAUTERMINAL concernant les données de compte, sessions, paiements et prestataires.",
    },
    "risk_title": {
        "title": "Disclaimer trading et risques",
        "kicker": "RISQUES",
        "description": "Avertissement sur les risques liés au trading, aux données de marché et à l'utilisation des outils XAUTERMINAL.",
    },
}

FX_MARKET_PAIRS = [
    {
        "slug": "eurusd",
        "pair": "EUR/USD",
        "rank": 1,
        "share": "21.2%",
        "tv_symbol": "FX:EURUSD",
        "fr": {
            "name": "Euro / dollar américain",
            "headline": "La paire centrale du marché Forex mondial",
            "intro": "EUR/USD concentre la liquidité entre les deux plus grandes zones monétaires. Elle réagit fortement aux écarts de politique Fed/BCE, aux taux, au DXY, aux surprises d'inflation et au sentiment de risque global.",
            "role": "Paire de référence pour lire la force relative euro-dollar et l'appétit pour le dollar.",
            "drivers": ["Fed vs BCE", "DXY", "Taux US et européens", "Inflation", "PMI et croissance"],
            "terminal": "Dans XAUTERMINAL, EUR/USD peut être suivi avec le graphique TradingView, les news dollar/euro, le calendrier US/EU et une lecture de contexte adaptée au symbole.",
        },
        "en": {
            "name": "Euro / US dollar",
            "headline": "The central pair of the global Forex market",
            "intro": "EUR/USD concentrates liquidity between the two largest monetary areas. It reacts strongly to Fed/ECB policy spreads, yields, DXY, inflation surprises and global risk sentiment.",
            "role": "Reference pair for reading euro-dollar relative strength and dollar appetite.",
            "drivers": ["Fed vs ECB", "DXY", "US and European yields", "Inflation", "PMIs and growth"],
            "terminal": "In XAUTERMINAL, EUR/USD can be followed with TradingView charting, dollar/euro news, the US/EU calendar and a context read adapted to the symbol.",
        },
    },
    {
        "slug": "usdjpy",
        "pair": "USD/JPY",
        "rank": 2,
        "share": "14.3%",
        "tv_symbol": "FX:USDJPY",
        "fr": {
            "name": "Dollar américain / yen japonais",
            "headline": "La paire du dollar, des taux US et du yen",
            "intro": "USD/JPY est très sensible aux rendements américains, aux attentes de la BoJ, aux interventions verbales japonaises et aux mouvements risk-on/risk-off.",
            "role": "Paire majeure pour suivre le carry trade, les taux US et la pression sur le yen.",
            "drivers": ["US10Y", "BoJ", "Fed", "Différentiel de taux", "Risk sentiment"],
            "terminal": "Le terminal aide à croiser USD/JPY avec DXY, US10Y, news Fed/BoJ et calendrier US/JP.",
        },
        "en": {
            "name": "US dollar / Japanese yen",
            "headline": "The pair of the dollar, US yields and the yen",
            "intro": "USD/JPY is highly sensitive to US yields, Bank of Japan expectations, Japanese verbal intervention and risk-on/risk-off moves.",
            "role": "Major pair for tracking carry, US yields and pressure on the yen.",
            "drivers": ["US10Y", "BoJ", "Fed", "Yield spread", "Risk sentiment"],
            "terminal": "The terminal helps compare USD/JPY with DXY, US10Y, Fed/BoJ news and the US/JP calendar.",
        },
    },
    {
        "slug": "gbpusd",
        "pair": "GBP/USD",
        "rank": 3,
        "share": "7.6%",
        "tv_symbol": "FX:GBPUSD",
        "fr": {
            "name": "Livre sterling / dollar américain",
            "headline": "La paire sterling-dollar la plus suivie",
            "intro": "GBP/USD combine le dollar, la politique de la BoE, les données britanniques et le sentiment global. Elle peut être vive pendant Londres et autour des statistiques US.",
            "role": "Paire clé pour lire la livre face au dollar et les arbitrages Fed/BoE.",
            "drivers": ["BoE", "Fed", "Inflation UK", "DXY", "Session Londres"],
            "terminal": "XAUTERMINAL centralise le graphique, les news UK/US et le calendrier à surveiller avant de trader GBP/USD.",
        },
        "en": {
            "name": "British pound / US dollar",
            "headline": "The most followed sterling-dollar pair",
            "intro": "GBP/USD combines the dollar, Bank of England policy, UK data and global sentiment. It can be lively during London and around US releases.",
            "role": "Key pair for reading sterling against the dollar and Fed/BoE repricing.",
            "drivers": ["BoE", "Fed", "UK inflation", "DXY", "London session"],
            "terminal": "XAUTERMINAL centralizes charting, UK/US news and the calendar to watch before trading GBP/USD.",
        },
    },
    {
        "slug": "usdcny",
        "pair": "USD/CNY",
        "rank": 4,
        "share": "6%+",
        "tv_symbol": "FX_IDC:USDCNY",
        "fr": {
            "name": "Dollar américain / yuan chinois",
            "headline": "La paire Chine-dollar à surveiller",
            "intro": "USD/CNY reflète la relation dollar-yuan, les fixings de la PBoC, les flux commerciaux, la croissance chinoise et le niveau général du dollar.",
            "role": "Paire importante pour suivre le yuan, la Chine et les tensions dollar/Asie.",
            "drivers": ["PBoC", "DXY", "Croissance chinoise", "Commerce mondial", "Risk Asia"],
            "terminal": "La page publique donne le cadre; le terminal permet de suivre le symbole, les news Chine/US et les drivers associés.",
        },
        "en": {
            "name": "US dollar / Chinese yuan",
            "headline": "The China-dollar pair to watch",
            "intro": "USD/CNY reflects the dollar-yuan relationship, PBoC fixings, trade flows, Chinese growth and the broader dollar level.",
            "role": "Important pair for tracking the yuan, China and dollar/Asia tension.",
            "drivers": ["PBoC", "DXY", "Chinese growth", "Global trade", "Asia risk"],
            "terminal": "The public page gives the framework; the terminal lets users track the symbol, China/US news and related drivers.",
        },
    },
    {
        "slug": "usdcad",
        "pair": "USD/CAD",
        "rank": 5,
        "share": "5%+",
        "tv_symbol": "FX:USDCAD",
        "fr": {
            "name": "Dollar américain / dollar canadien",
            "headline": "Dollar, pétrole et Canada",
            "intro": "USD/CAD mélange le dollar américain, la politique de la BoC, les statistiques canadiennes et la sensibilité du CAD au pétrole.",
            "role": "Paire majeure pour suivre le CAD, le pétrole et les écarts Fed/BoC.",
            "drivers": ["BoC", "Fed", "Pétrole WTI", "Emploi Canada", "DXY"],
            "terminal": "XAUTERMINAL aide à croiser USD/CAD avec DXY, USOIL, news macro et calendrier US/CA.",
        },
        "en": {
            "name": "US dollar / Canadian dollar",
            "headline": "Dollar, oil and Canada",
            "intro": "USD/CAD blends the US dollar, Bank of Canada policy, Canadian data and the CAD's sensitivity to oil.",
            "role": "Major pair for tracking CAD, oil and Fed/BoC spreads.",
            "drivers": ["BoC", "Fed", "WTI oil", "Canada jobs", "DXY"],
            "terminal": "XAUTERMINAL helps compare USD/CAD with DXY, USOIL, macro news and the US/CA calendar.",
        },
    },
    {
        "slug": "audusd",
        "pair": "AUD/USD",
        "rank": 6,
        "share": "4%+",
        "tv_symbol": "FX:AUDUSD",
        "fr": {
            "name": "Dollar australien / dollar américain",
            "headline": "La paire cyclique Australie-dollar",
            "intro": "AUD/USD est sensible au dollar, à la RBA, aux matières premières, à la Chine et au sentiment de risque.",
            "role": "Paire utile pour lire la croissance globale, la Chine et les devises cycliques.",
            "drivers": ["RBA", "Chine", "Commodities", "DXY", "Risk sentiment"],
            "terminal": "Le terminal permet de suivre AUD/USD avec news global macro, calendrier US/AU et drivers risk-on/risk-off.",
        },
        "en": {
            "name": "Australian dollar / US dollar",
            "headline": "The cyclical Australia-dollar pair",
            "intro": "AUD/USD is sensitive to the dollar, RBA policy, commodities, China and risk sentiment.",
            "role": "Useful pair for reading global growth, China and cyclical currencies.",
            "drivers": ["RBA", "China", "Commodities", "DXY", "Risk sentiment"],
            "terminal": "The terminal helps follow AUD/USD with global macro news, US/AU calendar and risk-on/risk-off drivers.",
        },
    },
    {
        "slug": "usdchf",
        "pair": "USD/CHF",
        "rank": 7,
        "share": "3%+",
        "tv_symbol": "FX:USDCHF",
        "fr": {
            "name": "Dollar américain / franc suisse",
            "headline": "Dollar et devise refuge suisse",
            "intro": "USD/CHF combine la force du dollar, la politique de la BNS et la demande refuge liée au franc suisse.",
            "role": "Paire de refuge à surveiller en période de stress ou de repricing dollar.",
            "drivers": ["BNS", "Fed", "Risk-off", "DXY", "Inflation suisse"],
            "terminal": "XAUTERMINAL aide à contextualiser USD/CHF avec news risque, DXY, taux et calendrier.",
        },
        "en": {
            "name": "US dollar / Swiss franc",
            "headline": "Dollar and Swiss safe-haven currency",
            "intro": "USD/CHF combines dollar strength, Swiss National Bank policy and safe-haven demand around the franc.",
            "role": "Safe-haven pair to watch during stress or dollar repricing.",
            "drivers": ["SNB", "Fed", "Risk-off", "DXY", "Swiss inflation"],
            "terminal": "XAUTERMINAL helps contextualize USD/CHF with risk news, DXY, yields and calendar events.",
        },
    },
    {
        "slug": "usdhkd",
        "pair": "USD/HKD",
        "rank": 8,
        "share": "3%+",
        "tv_symbol": "FX_IDC:USDHKD",
        "fr": {
            "name": "Dollar américain / dollar de Hong Kong",
            "headline": "La paire du peg de Hong Kong",
            "intro": "USD/HKD est particulière car le dollar de Hong Kong évolue dans un régime de change encadré. Elle reste importante dans les volumes FX mondiaux.",
            "role": "Paire institutionnelle pour suivre le dollar, Hong Kong et les tensions de liquidité régionales.",
            "drivers": ["Peg HKD", "Liquidité HK", "DXY", "Taux US", "Asie"],
            "terminal": "La page sert de contexte public; le terminal permet de replacer USD/HKD dans le radar dollar/Asie.",
        },
        "en": {
            "name": "US dollar / Hong Kong dollar",
            "headline": "The Hong Kong peg pair",
            "intro": "USD/HKD is special because the Hong Kong dollar trades within a managed exchange-rate regime. It remains important in global FX volumes.",
            "role": "Institutional pair for tracking the dollar, Hong Kong and regional liquidity stress.",
            "drivers": ["HKD peg", "HK liquidity", "DXY", "US yields", "Asia"],
            "terminal": "The page gives public context; the terminal helps place USD/HKD inside the dollar/Asia radar.",
        },
    },
    {
        "slug": "nzdusd",
        "pair": "NZD/USD",
        "rank": 9,
        "share": "2%+",
        "tv_symbol": "FX:NZDUSD",
        "fr": {
            "name": "Dollar néo-zélandais / dollar américain",
            "headline": "La paire kiwi-dollar",
            "intro": "NZD/USD réagit au dollar, à la RBNZ, au risque global, à la Chine et aux matières premières agricoles.",
            "role": "Paire cyclique plus volatile, utile pour lire le risk appetite en FX.",
            "drivers": ["RBNZ", "DXY", "Chine", "Risk sentiment", "Données NZ"],
            "terminal": "Le terminal aide à suivre NZD/USD avec calendrier, news et drivers dollar/risk.",
        },
        "en": {
            "name": "New Zealand dollar / US dollar",
            "headline": "The kiwi-dollar pair",
            "intro": "NZD/USD reacts to the dollar, RBNZ policy, global risk, China and agricultural commodities.",
            "role": "More volatile cyclical pair, useful for reading FX risk appetite.",
            "drivers": ["RBNZ", "DXY", "China", "Risk sentiment", "NZ data"],
            "terminal": "The terminal helps follow NZD/USD with calendar, news and dollar/risk drivers.",
        },
    },
    {
        "slug": "eurjpy",
        "pair": "EUR/JPY",
        "rank": 10,
        "share": "2%+",
        "tv_symbol": "FX:EURJPY",
        "fr": {
            "name": "Euro / yen japonais",
            "headline": "Cross euro-yen et sentiment global",
            "intro": "EUR/JPY combine la BCE, la BoJ, les taux européens/japonais et la demande refuge sur le yen.",
            "role": "Cross majeur pour lire risk appetite, yen et divergence BCE/BoJ.",
            "drivers": ["BCE", "BoJ", "Risk sentiment", "Taux européens", "JPY refuge"],
            "terminal": "XAUTERMINAL peut adapter le contexte EUR/JPY et relier le graphique aux news BCE/BoJ.",
        },
        "en": {
            "name": "Euro / Japanese yen",
            "headline": "Euro-yen cross and global sentiment",
            "intro": "EUR/JPY combines the ECB, BoJ, European/Japanese yields and safe-haven demand for the yen.",
            "role": "Major cross for reading risk appetite, yen dynamics and ECB/BoJ divergence.",
            "drivers": ["ECB", "BoJ", "Risk sentiment", "European yields", "JPY haven"],
            "terminal": "XAUTERMINAL can adapt EUR/JPY context and link the chart to ECB/BoJ news.",
        },
    },
    {
        "slug": "eurgbp",
        "pair": "EUR/GBP",
        "rank": 11,
        "share": "2%+",
        "tv_symbol": "FX:EURGBP",
        "fr": {
            "name": "Euro / livre sterling",
            "headline": "Cross BCE-BoE",
            "intro": "EUR/GBP se concentre sur la comparaison euro-livre: croissance Europe/UK, inflation, BCE, BoE et flux de session Londres.",
            "role": "Cross important pour lire la divergence monétaire entre zone euro et Royaume-Uni.",
            "drivers": ["BCE", "BoE", "Inflation UK/EU", "PMI", "Session Londres"],
            "terminal": "Le terminal permet de suivre EUR/GBP sans tout ramener au dollar, avec une lecture croisée Europe/UK.",
        },
        "en": {
            "name": "Euro / British pound",
            "headline": "ECB-BoE cross",
            "intro": "EUR/GBP focuses on the euro-sterling comparison: Europe/UK growth, inflation, ECB, BoE and London-session flows.",
            "role": "Important cross for reading monetary divergence between the euro area and the UK.",
            "drivers": ["ECB", "BoE", "UK/EU inflation", "PMIs", "London session"],
            "terminal": "The terminal helps follow EUR/GBP without reducing everything to the dollar, with a Europe/UK cross-read.",
        },
    },
    {
        "slug": "gbpjpy",
        "pair": "GBP/JPY",
        "rank": 12,
        "share": "1%+",
        "tv_symbol": "FX:GBPJPY",
        "fr": {
            "name": "Livre sterling / yen japonais",
            "headline": "Cross très actif et souvent volatil",
            "intro": "GBP/JPY attire beaucoup de traders actifs grâce à sa volatilité. La paire combine livre, yen, BoE, BoJ, risk sentiment et mouvements de taux.",
            "role": "Cross populaire pour la volatilité, mais qui demande une lecture stricte du risque.",
            "drivers": ["BoE", "BoJ", "Risk sentiment", "Taux UK/JP", "Volatilité"],
            "terminal": "XAUTERMINAL aide à structurer GBP/JPY avec charting, news, calendrier UK/JP et biais de contexte.",
        },
        "en": {
            "name": "British pound / Japanese yen",
            "headline": "Very active and often volatile cross",
            "intro": "GBP/JPY attracts many active traders because of its volatility. The pair combines sterling, yen, BoE, BoJ, risk sentiment and yield moves.",
            "role": "Popular volatility cross, but it requires strict risk reading.",
            "drivers": ["BoE", "BoJ", "Risk sentiment", "UK/JP yields", "Volatility"],
            "terminal": "XAUTERMINAL helps structure GBP/JPY with charting, news, UK/JP calendar and context bias.",
        },
    },
]

FX_MARKET_BY_SLUG = {pair["slug"]: pair for pair in FX_MARKET_PAIRS}

SEO_CONTENT_PAGES = {
    "terminal_xauusd": {
        "path": "/terminal-xauusd",
        "title": "Terminal XAU/USD pour suivre l'or, le dollar et les taux",
        "description": "Comprendre comment XAUTERMINAL aide à suivre XAU/USD avec charting, news macro, calendrier économique, DXY, taux US et drivers de marché.",
        "kicker": "XAU/USD",
        "h1": "Terminal XAU/USD: suivre l'or avec une lecture macro claire",
        "intro": "XAU/USD réagit souvent à plusieurs forces en même temps: dollar américain, taux US, inflation, discours de la Fed, stress géopolitique et momentum court terme. XAUTERMINAL rassemble ces informations dans une interface pensée pour préparer une décision, pas pour remplacer une stratégie.",
        "sections": [
            (
                "Pourquoi XAU/USD demande une lecture multi-facteurs",
                "L'or peut monter parce que le dollar baisse, parce que les rendements réels se détendent, parce qu'un risque géopolitique soutient la demande refuge ou simplement parce que le momentum technique domine la séance. Regarder uniquement le graphique peut donc laisser une partie importante du contexte de côté.",
            ),
            (
                "Ce que le terminal centralise pour l'or",
                "Le profil XAU/USD regroupe le charting TradingView, les news liées à la Fed, au dollar, aux taux, à l'inflation et à la géopolitique, le calendrier économique US, une watchlist orientée or et un Bias Desk qui synthétise les drivers principaux.",
            ),
            (
                "Comment utiliser cette page dans une routine",
                "Avant une session, vérifie les événements US à venir, lis les news prioritaires, observe DXY et US10Y, puis compare ce contexte avec le mouvement de XAU/USD. L'objectif est d'éviter d'entrer sans savoir quel facteur domine le marché.",
            ),
            (
                "Limite importante",
                "Le terminal ne fournit pas de conseil financier ni de signal garanti. Il sert à structurer l'information et à gagner du temps dans l'analyse. La décision, le risque et la gestion de position restent sous ta responsabilité.",
            ),
            (
                "Routine simple avant une session XAU/USD",
                "Une routine efficace commence par les événements macro du jour, puis les thèmes dominants: inflation, Fed, dollar, rendements, risque géopolitique et sentiment global. Ensuite seulement, le graphique permet de vérifier si le prix confirme ou contredit ce contexte.",
            ),
            (
                "Pourquoi XAUTERMINAL existe",
                "L'objectif n'est pas d'ajouter un écran de plus, mais de réduire les allers-retours entre calendrier, news, watchlist, graphique et notes de contexte. Une lecture plus organisée aide à éviter les décisions prises uniquement sous pression ou sur une seule information.",
            ),
        ],
        "links": [
            ("/#pricing", "Démarrer l'essai XAUTERMINAL"),
            ("/calendrier-economique-or", "Lire le calendrier économique pour l'or"),
            ("/guide/trading-or-macro", "Comprendre la lecture macro de l'or"),
        ],
        "faqs": [
            (
                "XAUTERMINAL est-il seulement fait pour XAU/USD ?",
                "Non. XAU/USD est le marché central du projet, mais le terminal propose aussi des profils Forex, indices et crypto pour adapter les news, la watchlist et le contexte.",
            ),
            (
                "Le terminal remplace-t-il une stratégie de trading ?",
                "Non. Il sert à organiser l'information et à préparer une décision. La stratégie, le timing, le risque et l'exécution restent sous la responsabilité de l'utilisateur.",
            ),
        ],
    },
    "calendrier_or": {
        "path": "/calendrier-economique-or",
        "title": "Calendrier économique pour trader l'or: CPI, NFP, Fed et taux US",
        "description": "Guide pratique pour lire le calendrier économique quand on suit l'or et XAU/USD: inflation, NFP, Fed, taux US, dollar et volatilité.",
        "kicker": "CALENDRIER ÉCONOMIQUE",
        "h1": "Calendrier économique pour l'or: les événements à surveiller sur XAU/USD",
        "intro": "Sur XAU/USD, certaines statistiques peuvent changer brutalement la lecture du marché. L'inflation, l'emploi américain, les décisions de la Fed et les publications liées à la croissance influencent le dollar, les taux et donc l'or.",
        "sections": [
            (
                "Les publications qui comptent le plus",
                "Les traders sur l'or surveillent notamment le CPI, le PCE, les NFP, le chômage, les ventes au détail, les PMI, les décisions FOMC et les discours de membres de la Fed. Ces événements peuvent modifier les anticipations de taux et déclencher une forte volatilité.",
            ),
            (
                "Actual, forecast, previous: quoi comparer ?",
                "Une publication se lit rarement seule. Il faut comparer le chiffre publié au consensus et au chiffre précédent. Un résultat supérieur aux attentes peut soutenir le dollar ou les taux selon le contexte, ce qui peut peser sur l'or. L'inverse peut soutenir XAU/USD.",
            ),
            (
                "Pourquoi le timing est important",
                "Les minutes avant et après une publication importante sont souvent instables. Le terminal met en avant les événements à fort impact et les blocs de release pour éviter de découvrir trop tard qu'une statistique majeure arrive.",
            ),
            (
                "Utiliser le calendrier avec le reste du contexte",
                "Un calendrier seul ne suffit pas. Il faut le croiser avec les news, DXY, US10Y, le niveau de volatilité et le comportement du prix. C'est cette combinaison que XAUTERMINAL cherche à rendre plus lisible.",
            ),
            (
                "Préparer les annonces plutôt que les subir",
                "L'intérêt d'un calendrier n'est pas seulement de connaître l'heure d'une annonce. Il permet de décider à l'avance si l'on évite une zone de volatilité, si l'on attend la réaction du marché ou si l'on adapte son plan de risque.",
            ),
            (
                "Les annonces ne se lisent pas toutes pareil",
                "Une même surprise peut avoir un effet différent selon le contexte. Un CPI supérieur aux attentes ne produit pas toujours la même réaction si le marché anticipe déjà une Fed restrictive ou si le dollar est en correction depuis plusieurs séances.",
            ),
        ],
        "links": [
            ("/#pricing", "Tester le terminal complet"),
            ("/terminal-xauusd", "Suivre XAU/USD dans le terminal"),
            ("/news-forex-or", "Comprendre les news macro pour l'or"),
        ],
        "faqs": [
            (
                "Quels événements économiques influencent le plus l'or ?",
                "Les publications américaines comme CPI, PCE, NFP, chômage, PMI, ventes au détail, décisions FOMC et discours de la Fed sont souvent centrales car elles influencent le dollar et les taux.",
            ),
            (
                "Faut-il trader pendant les annonces ?",
                "Pas nécessairement. Beaucoup de traders préfèrent attendre que la volatilité initiale se calme. Le calendrier sert d'abord à connaître le risque événementiel avant de prendre une décision.",
            ),
        ],
    },
    "news_forex_or": {
        "path": "/news-forex-or",
        "title": "News Forex et or: filtrer les informations utiles pour XAU/USD",
        "description": "Comment filtrer les news forex, dollar, Fed, inflation, géopolitique et taux US pour mieux comprendre les mouvements de l'or et de XAU/USD.",
        "kicker": "NEWS MACRO",
        "h1": "News Forex et or: filtrer le bruit pour comprendre XAU/USD",
        "intro": "Les news de marché arrivent vite et dans tous les sens. Pour l'or, l'enjeu n'est pas de tout lire, mais d'identifier ce qui peut réellement changer le dollar, les taux, l'appétit pour le risque ou la demande refuge.",
        "sections": [
            (
                "Les familles de news à prioriser",
                "Pour XAU/USD, les catégories les plus utiles sont souvent la Fed, l'inflation, l'emploi américain, les rendements obligataires, le dollar, la géopolitique, les banques centrales et les surprises de données macro.",
            ),
            (
                "Pourquoi une news peut être importante sans bouger le marché",
                "Une information peut être vraie mais déjà intégrée par les prix. Le terminal aide à distinguer les news récentes, les sujets officiels, les informations répétées par plusieurs sources et les éléments potentiellement market moving.",
            ),
            (
                "Croiser les news avec DXY et US10Y",
                "Une news hawkish sur la Fed peut soutenir le dollar et les rendements, ce qui met souvent l'or sous pression. Une news dovish ou un stress géopolitique peut produire l'effet inverse. La watchlist permet de vérifier rapidement cette cohérence.",
            ),
            (
                "Créer une routine plus calme",
                "L'objectif n'est pas de réagir à chaque headline. Une bonne routine consiste à lire les priorités, repérer le thème dominant, vérifier si le prix confirme, puis attendre un setup compatible avec son propre plan.",
            ),
            (
                "Différencier information et décision",
                "Une headline peut expliquer un mouvement sans offrir une opportunité exploitable. XAUTERMINAL aide à classer l'information, mais la décision doit venir d'un plan cohérent entre contexte, prix, risque et horizon de temps.",
            ),
            (
                "Pourquoi le bruit coûte cher",
                "Trop de sources ouvertes en même temps peuvent pousser à surinterpréter chaque variation. Un flux mieux organisé permet de se concentrer sur les thèmes réellement capables de modifier le dollar, les taux ou la demande refuge.",
            ),
        ],
        "links": [
            ("/#pricing", "Essayer XAUTERMINAL"),
            ("/calendrier-economique-or", "Comparer avec le calendrier économique"),
            ("/guide/trading-or-macro", "Construire une lecture macro"),
        ],
        "faqs": [
            (
                "Quelles news suivre pour XAU/USD ?",
                "Les news liées à la Fed, à l'inflation, à l'emploi américain, au dollar, aux rendements obligataires, à la géopolitique et au sentiment de risque sont souvent les plus utiles.",
            ),
            (
                "Une news importante fait-elle toujours bouger l'or ?",
                "Non. Si l'information est déjà intégrée par les prix ou si un autre thème domine le marché, la réaction peut être faible, retardée ou opposée à l'intuition initiale.",
            ),
        ],
    },
    "guide_trading_or_macro": {
        "path": "/guide/trading-or-macro",
        "title": "Guide macro pour trader l'or: dollar, taux, inflation et Fed",
        "description": "Guide pédagogique pour comprendre les principaux drivers macro de l'or: DXY, taux US, inflation, Fed, stress de marché et momentum.",
        "kicker": "GUIDE MACRO",
        "h1": "Guide macro pour trader l'or: dollar, taux, inflation et Fed",
        "intro": "Trader l'or sans contexte macro peut devenir confus: le même mouvement de prix peut venir d'un dollar faible, d'une baisse des rendements, d'une surprise d'inflation ou d'un stress de marché. Ce guide résume les drivers à suivre avant d'utiliser le terminal.",
        "sections": [
            (
                "Dollar américain et or",
                "XAU/USD est coté en dollars. Quand le dollar se renforce fortement, l'or peut devenir plus difficile à acheter pour les autres devises, ce qui pèse souvent sur le prix. Quand le dollar se détend, XAU/USD peut respirer davantage.",
            ),
            (
                "Taux US et rendement réel",
                "L'or ne verse pas de rendement. Quand les taux et les rendements réels montent, les actifs rémunérés deviennent plus attractifs. Quand ils baissent, l'or peut redevenir plus compétitif, surtout si l'inflation ou le risque restent présents.",
            ),
            (
                "Fed, inflation et emploi",
                "La Fed influence les anticipations de taux. Les chiffres d'inflation et d'emploi modifient ces anticipations. C'est pour cela que CPI, PCE, NFP et FOMC sont souvent des moments clés pour XAU/USD.",
            ),
            (
                "Momentum et confirmation",
                "Le contexte macro donne une direction probable, mais le prix doit confirmer. Le Bias Desk et les drivers du terminal servent à organiser cette lecture: macro, momentum, risque événementiel et watchlist.",
            ),
            (
                "Construire un scénario plutôt qu'une prédiction",
                "Une lecture macro utile ne cherche pas à deviner parfaitement le futur. Elle prépare plusieurs scénarios: dollar fort, détente des taux, surprise inflation, stress de marché ou absence de catalyseur clair.",
            ),
            (
                "Relier macro et exécution",
                "Le contexte aide à savoir où concentrer son attention, mais il ne suffit pas pour entrer en position. L'exécution demande un plan, un niveau d'invalidation, une taille adaptée et une acceptation claire du risque.",
            ),
        ],
        "links": [
            ("/#pricing", "Tester XAUTERMINAL"),
            ("/terminal-xauusd", "Voir l'approche XAU/USD"),
            ("/news-forex-or", "Lire les news macro utiles"),
        ],
        "faqs": [
            (
                "Quels sont les grands drivers macro de l'or ?",
                "Les plus importants sont souvent le dollar américain, les taux US, les rendements réels, l'inflation, la Fed, la géopolitique, le stress de marché et le momentum du prix.",
            ),
            (
                "La macro suffit-elle pour trader l'or ?",
                "Non. La macro donne un cadre de lecture, mais le prix, la volatilité, la liquidité, le timing et la gestion du risque restent indispensables.",
            ),
        ],
    },
    "routine_trading_xauusd": {
        "path": "/guides/routine-trading-xauusd",
        "title": "Routine trading XAU/USD: préparer une session avec méthode",
        "description": "Méthode concrète pour préparer une session XAU/USD avec calendrier économique, news macro, DXY, taux US, Bias Desk et niveaux de risque.",
        "kicker": "ROUTINE XAU/USD",
        "h1": "Routine trading XAU/USD: préparer une session sans se disperser",
        "intro": "Une routine de marché sert à réduire le bruit avant d'ouvrir un graphique. Sur XAU/USD, l'objectif est de comprendre le thème dominant de la séance: dollar, taux, inflation, Fed, stress de marché ou simple momentum technique.",
        "sections": [
            (
                "Commencer par le calendrier",
                "Avant de regarder le prix, vérifie les annonces à venir: CPI, PCE, NFP, chômage, PMI, ventes au détail, FOMC et discours de la Fed. Une statistique majeure peut rendre un setup propre beaucoup moins lisible quelques minutes plus tard.",
            ),
            (
                "Identifier le thème macro du jour",
                "Lis les news prioritaires et cherche le fil conducteur: Fed plus restrictive, dollar sous pression, rendements en hausse, stress géopolitique ou absence de catalyseur clair. Une séance sans thème dominant demande souvent plus de patience.",
            ),
            (
                "Comparer XAU/USD avec DXY et US10Y",
                "Si l'or monte pendant que DXY et les taux baissent, le mouvement est plus cohérent. Si les signaux divergent, il vaut mieux éviter de conclure trop vite. Le but est de savoir si le prix est porté ou contrarié par ses drivers principaux.",
            ),
            (
                "Utiliser le Bias Desk comme synthèse",
                "Le Bias Desk n'est pas un signal automatique. Il aide à regrouper momentum, macro, risk tone et risque événementiel. S'il affiche WAIT, cela peut simplement signifier que les conditions ne sont pas assez alignées.",
            ),
            (
                "Finir par le plan de risque",
                "Une fois le contexte compris, le graphique sert à définir le timing, l'invalidation et la taille. La meilleure lecture macro ne protège pas d'une mauvaise exécution ou d'un risque trop grand.",
            ),
        ],
        "links": [
            ("/#pricing", "Tester le terminal complet"),
            ("/calendrier-economique-or", "Lire le calendrier économique"),
            ("/news-forex-or", "Filtrer les news macro"),
        ],
        "faqs": [
            (
                "Combien de temps doit durer une routine XAU/USD ?",
                "Une routine utile peut durer quelques minutes si elle est structurée: calendrier, news, DXY, US10Y, Bias Desk puis graphique. L'important est la régularité, pas la durée.",
            ),
            (
                "Faut-il suivre toutes les news avant de trader ?",
                "Non. Il faut surtout repérer les thèmes capables de changer le dollar, les taux, la demande refuge ou la volatilité. Lire trop de sources peut créer plus de confusion que de clarté.",
            ),
        ],
    },
    "dxy_taux_or": {
        "path": "/guides/dxy-taux-us-or",
        "title": "DXY, taux US et or: comprendre les relations avec XAU/USD",
        "description": "Guide XAUTERMINAL pour comprendre comment le dollar, les rendements US, la Fed et le sentiment de risque influencent l'or et XAU/USD.",
        "kicker": "DXY ET TAUX US",
        "h1": "DXY, taux US et or: comprendre les relations avec XAU/USD",
        "intro": "L'or ne bouge pas dans le vide. Même quand le graphique semble clair, XAU/USD reste influencé par le dollar américain, les rendements obligataires, les anticipations de taux et le niveau de stress de marché.",
        "sections": [
            (
                "Pourquoi le dollar compte autant",
                "XAU/USD est coté en dollars. Un dollar fort peut rendre l'or plus cher pour les acheteurs hors dollar et peser sur le prix. Un dollar plus faible peut au contraire soutenir le métal, surtout si les autres facteurs ne s'y opposent pas.",
            ),
            (
                "Le rôle des taux US",
                "L'or ne verse pas de rendement. Quand les rendements US montent, les actifs rémunérés deviennent plus compétitifs. Quand ils baissent, l'or peut retrouver de l'attrait, notamment si le marché anticipe une Fed moins restrictive.",
            ),
            (
                "Quand DXY et taux ne racontent pas la même histoire",
                "Il arrive que le dollar monte alors que les taux baissent, ou l'inverse. Dans ce cas, la lecture devient moins directe. Le trader doit chercher quel driver domine réellement le mouvement de XAU/USD.",
            ),
            (
                "Ajouter le sentiment de risque",
                "En période de stress, l'or peut être soutenu même si certains drivers semblent défavorables. À l'inverse, une séance très risk-on peut réduire la demande refuge. C'est pour cela qu'une lecture multi-facteurs est nécessaire.",
            ),
            (
                "Comment XAUTERMINAL organise cette lecture",
                "Le terminal regroupe DXY, US10Y, news macro, calendrier économique et Bias Desk. L'idée est de vérifier rapidement si les mouvements se confirment ou se contredisent avant de prendre une décision.",
            ),
        ],
        "links": [
            ("/terminal-xauusd", "Voir l'approche XAU/USD"),
            ("/guide/trading-or-macro", "Lire le guide macro"),
            ("/#pricing", "Essayer XAUTERMINAL"),
        ],
        "faqs": [
            (
                "XAU/USD baisse-t-il toujours quand DXY monte ?",
                "Non. C'est une relation fréquente mais pas mécanique. Les taux, la Fed, le risque géopolitique et le momentum peuvent modifier ou retarder la réaction.",
            ),
            (
                "Les taux US sont-ils plus importants que le dollar ?",
                "Cela dépend du contexte. Certaines séances sont dominées par le dollar, d'autres par les rendements, la Fed ou le sentiment de risque. L'intérêt est de comparer ces forces ensemble.",
            ),
        ],
    },
    "bias_desk": {
        "path": "/guides/bias-desk-trading",
        "title": "Bias Desk trading: lire les drivers sans confondre outil et signal",
        "description": "Comprendre comment utiliser un Bias Desk pour organiser les drivers de marché sans transformer une synthèse macro en signal de trading automatique.",
        "kicker": "BIAS DESK",
        "h1": "Bias Desk trading: lire les drivers sans confondre outil et signal",
        "intro": "Un Bias Desk sert à résumer une lecture de marché: momentum, macro, risque événementiel, sentiment et drivers principaux. Il ne remplace pas une stratégie, mais il peut aider à éviter les décisions prises sur une seule information.",
        "sections": [
            (
                "Ce qu'un bias veut dire",
                "Un bias est une orientation de contexte, pas une certitude. Bullish signifie que plusieurs éléments soutiennent plutôt la hausse. Bearish signifie que les pressions baissières dominent. Neutral ou WAIT indique souvent un manque d'alignement.",
            ),
            (
                "Pourquoi les drivers sont plus utiles que le score seul",
                "Le score donne une synthèse rapide, mais les raisons sont plus importantes. Un trader doit savoir si le bias vient du dollar, des taux, du momentum, d'une news ou d'un risque événementiel.",
            ),
            (
                "Lire le risque événementiel",
                "Un contexte favorable peut devenir dangereux juste avant une annonce majeure. Si le calendrier indique un risque élevé, la bonne décision peut être d'attendre, même si le reste du marché semble aligné.",
            ),
            (
                "Utiliser le bias avec le graphique",
                "Le graphique reste indispensable pour le timing. Le bias aide à préparer le scénario; le prix aide à décider si ce scénario mérite d'être exécuté, invalidé ou simplement observé.",
            ),
            (
                "Les limites d'une synthèse automatique",
                "Aucun outil ne peut comprendre parfaitement chaque nuance de marché. Le Bias Desk doit être traité comme une aide à la lecture, avec une vérification humaine et une gestion du risque indépendante.",
            ),
        ],
        "links": [
            ("/terminal-xauusd", "Voir le terminal XAU/USD"),
            ("/guides/routine-trading-xauusd", "Construire une routine"),
            ("/risk-disclaimer", "Lire le disclaimer trading"),
        ],
        "faqs": [
            (
                "Le Bias Desk donne-t-il des signaux d'achat ou de vente ?",
                "Non. Il organise les drivers de marché. La décision d'entrer, sortir ou rester à l'écart doit venir de ta stratégie, de ton timing et de ta gestion du risque.",
            ),
            (
                "Pourquoi le Bias Desk affiche parfois WAIT ?",
                "WAIT apparaît quand les drivers sont mixtes, quand la confiance est insuffisante ou quand un risque événementiel rend la lecture trop instable.",
            ),
        ],
    },
}

RESOURCE_PAGE_ORDER = [
    "terminal_xauusd",
    "calendrier_or",
    "news_forex_or",
    "guide_trading_or_macro",
]

GUIDE_PAGE_ORDER = [
    "routine_trading_xauusd",
    "dxy_taux_or",
    "bias_desk",
    "guide_trading_or_macro",
]


def content_page(page_key: str) -> str:
    page = SEO_CONTENT_PAGES[page_key]
    prefix = f"seo_{page_key}"
    canonical = absolute_url(page["path"])
    escaped_title = escape(page["title"], quote=True)
    escaped_description = escape(page["description"], quote=True)
    escaped_h1 = escape(page["h1"])
    escaped_intro = escape(page["intro"])
    sections = "\n".join(
        f"""                <section class="article-section-card" id="section-{index}">
                    <span>{index:02d}</span>
                    <h2 data-i18n="{prefix}_section{index}_title">{escape(title)}</h2>
                    <p data-i18n="{prefix}_section{index}_copy">{escape(copy)}</p>
                </section>"""
        for index, (title, copy) in enumerate(page["sections"], start=1)
    )
    section_nav = "\n".join(
        f"""                    <a href="#section-{index}" data-i18n="{prefix}_section{index}_title">{escape(title)}</a>"""
        for index, (title, _) in enumerate(page["sections"], start=1)
    )
    faqs = page.get("faqs", [])
    faq_html = "\n".join(
        f"""                    <article>
                <h3 data-i18n="{prefix}_faq{index}_question">{escape(question)}</h3>
                <p data-i18n="{prefix}_faq{index}_answer">{escape(answer)}</p>
                    </article>"""
        for index, (question, answer) in enumerate(faqs, start=1)
    )
    faq_section = f"""                <section class="resource-faq">
                    <div class="landing-kicker" data-i18n="seo_faq_kicker">FAQ</div>
                    <h2 data-i18n="seo_faq_title">Questions fréquentes</h2>
{faq_html}
                </section>""" if faq_html else ""
    links = "\n".join(
        f'<a class="resource-link-button" href="{escape(href, quote=True)}" data-i18n="{prefix}_link{index}">{escape(label)}</a>'
        for index, (href, label) in enumerate(page["links"], start=1)
    )
    featured_links = "\n".join(
        f"""                    <a href="{escape(href, quote=True)}" data-i18n="{prefix}_link{index}">{escape(label)}</a>"""
        for index, (href, label) in enumerate(page["links"], start=1)
    )
    related_links = ", ".join(label for _, label in page["links"])
    structured_graph = [
        {
            "@type": "Article",
            "headline": page["h1"],
            "description": page["description"],
            "url": canonical,
            "author": {
                "@type": "Person",
                "name": LEGAL_PUBLISHER_NAME,
            },
            "publisher": {
                "@type": "Organization",
                "name": LEGAL_BUSINESS_NAME,
                "url": APP_BASE_URL,
                "logo": absolute_url("/static/icon-192x192.png"),
            },
            "mainEntityOfPage": canonical,
            "inLanguage": "fr-FR",
            "about": related_links,
        }
    ]
    if faqs:
        structured_graph.append(
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": question,
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": answer,
                        },
                    }
                    for question, answer in faqs
                ],
            }
        )
    structured_data = json.dumps(
        {
            "@context": "https://schema.org",
            "@graph": structured_graph,
        },
        ensure_ascii=False,
    )
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title data-i18n="{prefix}_title">{escaped_title}</title>
    <meta name="description" content="{escaped_description}" data-i18n-content="{prefix}_description">
    <link rel="canonical" href="{canonical}">
    <meta name="robots" content="index,follow">
    <meta property="og:type" content="article">
    <meta property="og:site_name" content="XAUTERMINAL">
    <meta property="og:title" content="{escaped_title}" data-i18n-content="{prefix}_title">
    <meta property="og:description" content="{escaped_description}" data-i18n-content="{prefix}_description">
    <meta property="og:url" content="{canonical}">
    <meta property="og:image" content="{absolute_url('/static/icon-192x192.png')}">
    <meta name="twitter:card" content="summary">
{FAVICON_LINKS}
    <link rel="stylesheet" href="/static/styles.css">
    <script type="application/ld+json">{structured_data}</script>
</head>
<body class="legal-body">
    <header class="landing-nav">
        <a class="landing-brand" href="/" aria-label="XAUTERMINAL">
            {BRAND_MARKUP}
        </a>
        <nav class="landing-nav-actions" aria-label="Navigation principale">
            <a href="/#features" data-i18n="nav_tools">Outils</a>
            <a href="/marches" data-i18n="nav_markets">Marchés</a>
            <a href="/market-pulse" data-i18n="nav_pulse">Market Pulse</a>
            <a href="/guides" data-i18n="nav_guides">Guides</a>
            <a href="/#pricing" data-i18n="nav_pricing">Formules</a>
            <a href="/support" data-i18n="nav_support">Support</a>
            <a href="/terminal" data-i18n="nav_terminal">Ouvrir le terminal</a>
            <button type="button" class="landing-lang" data-lang-toggle>EN</button>
        </nav>
    </header>
    <main class="legal-page article-page">
        <section class="article-hero">
            <div class="article-hero-copy">
                <div class="landing-kicker" data-i18n="{prefix}_kicker">{escape(page["kicker"])}</div>
                <h1 data-i18n="{prefix}_h1">{escaped_h1}</h1>
                <p data-i18n="{prefix}_intro">{escaped_intro}</p>
                <div class="landing-actions">{links}</div>
            </div>
            <aside class="article-hero-panel" aria-label="Résumé">
                <span data-i18n="article_panel_kicker">À LIRE AVEC</span>
                <strong>XAUTERMINAL</strong>
                <p data-i18n="article_panel_copy">Utilise cette ressource avec le calendrier, les news, les graphiques et le Bias Desk pour garder une lecture de marché structurée.</p>
            </aside>
        </section>
        <div class="article-layout">
            <aside class="article-sidebar" aria-label="Sommaire">
                <span data-i18n="article_summary">Sommaire</span>
                <nav>
{section_nav}
                </nav>
                <div class="article-related">
                    <strong data-i18n="article_related">Liens utiles</strong>
{featured_links}
                </div>
            </aside>
            <div class="article-content">
{sections}
{faq_section}
                <section class="legal-contact article-cta">
                    <h2 data-i18n="seo_continue_title">Continuer avec XAUTERMINAL</h2>
                    <p data-i18n="seo_continue_copy">Ces ressources sont pensées pour être utilisées ensemble: contexte macro, calendrier économique, news filtrées et charting. Pour tester l'espace complet, reviens sur la landing et démarre l'essai depuis le parcours officiel.</p>
                    <div class="landing-actions">{links}</div>
                </section>
            </div>
        </div>
    </main>
{PUBLIC_FOOTER}
    <script src="/static/landing.js"></script>
</body>
</html>"""


def resources_page() -> str:
    canonical = absolute_url("/ressources")
    pulse_row = """        <article class="resource-row">
            <div>
                <span data-i18n="pulse_page_kicker">MARKET PULSE</span>
                <h2><a href="/market-pulse" data-i18n="pulse_page_h1">Le briefing de marché avant d'ouvrir le terminal</a></h2>
                <p data-i18n="pulse_page_description">Market Pulse XAUTERMINAL synthétise le contexte macro, les actifs à surveiller, les news importantes et le calendrier économique avant une session de trading.</p>
            </div>
            <a class="resource-cta" href="/market-pulse" data-i18n="resources_page_read">Lire</a>
        </article>"""
    content_rows = "\n".join(
        f"""        <article class="resource-row">
            <div>
                <span data-i18n="seo_{key}_kicker">{escape(SEO_CONTENT_PAGES[key]["kicker"])}</span>
                <h2><a href="{escape(SEO_CONTENT_PAGES[key]["path"], quote=True)}" data-i18n="seo_{key}_h1">{escape(SEO_CONTENT_PAGES[key]["h1"])}</a></h2>
                <p data-i18n="seo_{key}_description">{escape(SEO_CONTENT_PAGES[key]["description"])}</p>
            </div>
            <a class="resource-cta" href="{escape(SEO_CONTENT_PAGES[key]["path"], quote=True)}" data-i18n="resources_page_read">Lire</a>
        </article>"""
        for key in RESOURCE_PAGE_ORDER
    )
    rows = f"{pulse_row}\n{content_rows}"
    structured_data = json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "name": "Ressources XAUTERMINAL",
            "description": "Guides publics pour comprendre XAU/USD, les news macro, le calendrier économique et les drivers de l'or.",
            "url": canonical,
            "hasPart": [
                {
                    "@type": "WebPage",
                    "headline": "Market Pulse XAUTERMINAL",
                    "url": absolute_url("/market-pulse"),
                }
            ] + [
                {
                    "@type": "Article",
                    "headline": SEO_CONTENT_PAGES[key]["h1"],
                    "url": absolute_url(SEO_CONTENT_PAGES[key]["path"]),
                }
                for key in RESOURCE_PAGE_ORDER
            ],
        },
        ensure_ascii=False,
    )
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title data-i18n="resources_page_title">Ressources trading macro, XAU/USD et calendrier économique - XAUTERMINAL</title>
    <meta name="description" content="Guides XAUTERMINAL pour comprendre XAU/USD, le calendrier économique de l'or, les news Forex et les principaux drivers macro." data-i18n-content="resources_page_description">
    <link rel="canonical" href="{canonical}">
    <meta name="robots" content="index,follow">
    <meta property="og:type" content="website">
    <meta property="og:site_name" content="XAUTERMINAL">
    <meta property="og:title" content="Ressources trading macro, XAU/USD et calendrier économique" data-i18n-content="resources_page_title">
    <meta property="og:description" content="Guides publics pour mieux lire l'or, les news macro, le calendrier économique et les drivers de marché." data-i18n-content="resources_page_description">
    <meta property="og:url" content="{canonical}">
    <meta property="og:image" content="{absolute_url('/static/icon-192x192.png')}">
    <meta name="twitter:card" content="summary">
{FAVICON_LINKS}
    <link rel="stylesheet" href="/static/styles.css">
    <script type="application/ld+json">{structured_data}</script>
</head>
<body class="legal-body">
    <header class="landing-nav">
        <a class="landing-brand" href="/" aria-label="XAUTERMINAL">
            {BRAND_MARKUP}
        </a>
        <nav class="landing-nav-actions" aria-label="Navigation principale">
            <a href="/#features" data-i18n="nav_tools">Outils</a>
            <a href="/marches" data-i18n="nav_markets">Marchés</a>
            <a href="/market-pulse" data-i18n="nav_pulse">Market Pulse</a>
            <a href="/guides" data-i18n="nav_guides">Guides</a>
            <a href="/#pricing" data-i18n="nav_pricing">Formules</a>
            <a href="/support" data-i18n="nav_support">Support</a>
            <a href="/terminal" data-i18n="nav_terminal">Ouvrir le terminal</a>
            <button type="button" class="landing-lang" data-lang-toggle>EN</button>
        </nav>
    </header>
    <main class="legal-page resource-index-page">
        <section class="article-hero resource-index-hero">
            <div class="article-hero-copy">
                <div class="landing-kicker" data-i18n="resources_kicker">RESSOURCES</div>
                <h1 data-i18n="resources_page_h1">Ressources trading macro, XAU/USD et calendrier économique</h1>
                <p data-i18n="resources_page_intro">Ces pages expliquent les concepts réellement liés à XAUTERMINAL: lecture macro de l'or, événements économiques, news Forex et organisation d'une routine de marché. Elles servent à comprendre le produit avant de l'utiliser dans le terminal.</p>
            </div>
            <aside class="article-hero-panel" aria-label="Ressources">
                <span data-i18n="resources_panel_kicker">HUB PUBLIC</span>
                <strong data-i18n="resources_panel_title">Comprendre avant d'agir</strong>
                <p data-i18n="resources_panel_copy">Chaque page relie une notion de marché à l'usage concret du terminal: news, calendrier, drivers et graphique.</p>
            </aside>
        </section>
        <section class="resource-list">
{rows}
        </section>
    </main>
{PUBLIC_FOOTER}
    <script src="/static/landing.js"></script>
</body>
</html>"""


def guides_page() -> str:
    canonical = absolute_url("/guides")
    rows = "\n".join(
        f"""        <article class="guide-card">
            <div class="guide-card-top">
                <span data-i18n="seo_{key}_kicker">{escape(SEO_CONTENT_PAGES[key]["kicker"])}</span>
                <a class="resource-link-button" href="{escape(SEO_CONTENT_PAGES[key]["path"], quote=True)}" data-i18n="resources_page_read">Lire</a>
            </div>
            <h2><a href="{escape(SEO_CONTENT_PAGES[key]["path"], quote=True)}" data-i18n="seo_{key}_h1">{escape(SEO_CONTENT_PAGES[key]["h1"])}</a></h2>
            <p data-i18n="seo_{key}_description">{escape(SEO_CONTENT_PAGES[key]["description"])}</p>
        </article>"""
        for key in GUIDE_PAGE_ORDER
    )
    structured_data = json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "name": "Guides trading XAUTERMINAL",
            "description": "Guides pratiques pour préparer une session XAU/USD, comprendre DXY, les taux US, les news macro et le Bias Desk.",
            "url": canonical,
            "hasPart": [
                {
                    "@type": "Article",
                    "headline": SEO_CONTENT_PAGES[key]["h1"],
                    "description": SEO_CONTENT_PAGES[key]["description"],
                    "url": absolute_url(SEO_CONTENT_PAGES[key]["path"]),
                }
                for key in GUIDE_PAGE_ORDER
            ],
        },
        ensure_ascii=False,
    )
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title data-i18n="guides_page_title">Guides trading XAU/USD, macro et Bias Desk - XAUTERMINAL</title>
    <meta name="description" content="Guides XAUTERMINAL pour préparer une session XAU/USD, comprendre DXY, les taux US, les news macro et utiliser un Bias Desk." data-i18n-content="guides_page_description">
    <link rel="canonical" href="{canonical}">
    <meta name="robots" content="index,follow">
    <meta property="og:type" content="website">
    <meta property="og:site_name" content="XAUTERMINAL">
    <meta property="og:title" content="Guides trading XAU/USD, macro et Bias Desk" data-i18n-content="guides_page_title">
    <meta property="og:description" content="Guides pratiques pour mieux préparer une session de trading avec le terminal XAUTERMINAL." data-i18n-content="guides_page_description">
    <meta property="og:url" content="{canonical}">
    <meta property="og:image" content="{absolute_url('/static/icon-192x192.png')}">
    <meta name="twitter:card" content="summary">
{FAVICON_LINKS}
    <link rel="stylesheet" href="/static/styles.css">
    <script type="application/ld+json">{structured_data}</script>
</head>
<body class="legal-body">
    <header class="landing-nav">
        <a class="landing-brand" href="/" aria-label="XAUTERMINAL">
            {BRAND_MARKUP}
        </a>
        <nav class="landing-nav-actions" aria-label="Navigation principale">
            <a href="/ressources" data-i18n="nav_resources">Ressources</a>
            <a href="/marches" data-i18n="nav_markets">Marchés</a>
            <a href="/market-pulse" data-i18n="nav_pulse">Market Pulse</a>
            <a href="/#pricing" data-i18n="nav_pricing">Formules</a>
            <a href="/support" data-i18n="nav_support">Support</a>
            <a href="/terminal" data-i18n="nav_terminal">Ouvrir le terminal</a>
            <button type="button" class="landing-lang" data-lang-toggle>EN</button>
        </nav>
    </header>
    <main class="legal-page guide-index-page">
        <section class="article-hero resource-index-hero">
            <div class="article-hero-copy">
                <div class="landing-kicker" data-i18n="guides_page_kicker">GUIDES TRADING</div>
                <h1 data-i18n="guides_page_h1">Guides trading XAU/USD, macro et Bias Desk</h1>
                <p data-i18n="guides_page_intro">Ces guides servent à construire une routine claire autour du terminal: préparer une session, lire DXY et les taux US, filtrer les news et utiliser le Bias Desk sans le confondre avec un signal automatique.</p>
            </div>
            <aside class="article-hero-panel" aria-label="Guides">
                <span data-i18n="guides_panel_kicker">ROUTINE</span>
                <strong data-i18n="guides_panel_title">Passer du bruit au plan</strong>
                <p data-i18n="guides_panel_copy">Les guides sont pensés comme des points d'entrée rapides avant d'ouvrir le terminal et d'observer les drivers réels.</p>
            </aside>
        </section>
        <section class="guide-grid">
{rows}
        </section>
        <section class="legal-contact">
            <h2 data-i18n="guides_page_next_title">Utiliser les guides avec le terminal</h2>
            <p data-i18n="guides_page_next_copy">Commence par comprendre la routine, puis ouvre le terminal pour vérifier le calendrier, les news, le graphique et les drivers en conditions réelles.</p>
            <div class="landing-actions">
                <a class="resource-cta" href="/#pricing" data-i18n="guides_page_trial">Tester XAUTERMINAL</a>
                <a class="resource-link-button" href="/ressources" data-i18n="guides_page_resources">Voir toutes les ressources</a>
            </div>
        </section>
    </main>
{PUBLIC_FOOTER}
    <script src="/static/landing.js"></script>
</body>
</html>"""


def market_pulse_page(pulse: dict) -> str:
    canonical = absolute_url("/market-pulse")
    summary = pulse.get("summary") or {}
    news_items = pulse.get("news") or []
    calendar_items = pulse.get("calendar") or []
    asset_items = pulse.get("assets") or []
    drivers = pulse.get("drivers") or []
    generated_at = escape(str(pulse.get("generated_at") or ""), quote=True)
    locked_note = escape(str(pulse.get("locked_note") or ""), quote=True)
    risk_score = int(summary.get("risk_score") or 0)
    risk_label = escape(str(summary.get("risk_label") or "Risque actif"))
    pulse_headline = escape(str(summary.get("headline") or "Marché à surveiller"))
    pulse_summary = escape(str(summary.get("summary") or "Le briefing public affiche une synthèse limitée."))
    pulse_action = escape(str(summary.get("action") or "WAIT"))
    pulse_bias = escape(str(summary.get("bias") or "Neutral"))
    news_html = "\n".join(
        f"""                <a class="pulse-live-row" href="{escape(item.get("url") or "#", quote=True)}" target="_blank" rel="noopener noreferrer">
                    <span>{escape(item.get("time") or "--:--")} · {escape(item.get("source") or "NEWS")}</span>
                    <strong>{escape(item.get("title") or "Market news")}</strong>
                    <em>{escape(str(item.get("priority") or "low").upper())}</em>
                </a>"""
        for item in news_items
    ) or """                <div class="pulse-live-empty">Aucune news prioritaire disponible pour le moment.</div>"""
    calendar_html = "\n".join(
        f"""                <article class="pulse-live-row locked">
                    <span>{escape(item.get("time") or "--:--")} · {escape(item.get("country") or "-")} · {escape(item.get("impact") or "-")}</span>
                    <strong>{escape(item.get("title") or "Economic event")}</strong>
                    <em>{escape(item.get("label") or "WATCH")}</em>
                </article>"""
        for item in calendar_items
    ) or """                <div class="pulse-live-empty">Aucun événement majeur détecté dans la fenêtre publique.</div>"""
    asset_html = "\n".join(
        f"""                <article>
                    <span>{escape(item.get("label") or "-")}</span>
                    <strong>{escape(item.get("direction") or "MIXED")} · {escape(item.get("activity") or "Watch")}</strong>
                    <em>{escape(item.get("note") or "Lecture complète dans le terminal")}</em>
                </article>"""
        for item in asset_items
    )
    driver_html = "\n".join(
        f"""                <article>
                    <span>{escape(driver.get("label") or "-")}</span>
                    <strong>{escape(str(driver.get("bias") or "neutral").upper())}</strong>
                    <em>{escape(driver.get("note") or "Driver à surveiller")}</em>
                </article>"""
        for driver in drivers
    )
    structured_data = json.dumps(
        {
            "@context": "https://schema.org",
            "@graph": [
                {
                    "@type": "WebPage",
                    "name": "Market Pulse XAUTERMINAL",
                    "description": "Market Pulse XAUTERMINAL synthétise le contexte macro, les actifs à surveiller, les news importantes et le calendrier économique avant une session de trading.",
                    "url": canonical,
                    "isPartOf": {
                        "@type": "WebSite",
                        "name": LEGAL_BUSINESS_NAME,
                        "url": APP_BASE_URL,
                    },
                    "publisher": {
                        "@type": "Organization",
                        "name": LEGAL_BUSINESS_NAME,
                        "url": APP_BASE_URL,
                        "logo": absolute_url("/static/icon-192x192.png"),
                    },
                    "inLanguage": "fr-FR",
                },
                {
                    "@type": "SoftwareApplication",
                    "name": "Market Pulse XAUTERMINAL",
                    "applicationCategory": "FinanceApplication",
                    "operatingSystem": "Web",
                    "url": canonical,
                    "description": "Briefing de marché pour organiser news, calendrier économique, drivers macro, watchlist et biais de contexte.",
                },
            ],
        },
        ensure_ascii=False,
    )
    pulse_cards = [
        (
            "pulse_page_card_calendar_title",
            "Calendrier à risque",
            "pulse_page_card_calendar_copy",
            "Repère les publications qui peuvent changer la volatilité: CPI, PCE, NFP, FOMC, PMI ou discours de banques centrales.",
        ),
        (
            "pulse_page_card_news_title",
            "News qui comptent",
            "pulse_page_card_news_copy",
            "Filtre les titres qui influencent vraiment le dollar, les taux, le sentiment de risque ou les actifs de ta watchlist.",
        ),
        (
            "pulse_page_card_drivers_title",
            "Drivers macro",
            "pulse_page_card_drivers_copy",
            "Compare DXY, US10Y, inflation, Fed, stress géopolitique et momentum pour comprendre ce qui domine la séance.",
        ),
        (
            "pulse_page_card_watchlist_title",
            "Radar actifs",
            "pulse_page_card_watchlist_copy",
            "Prépare les marchés à surveiller avant de passer au graphique: XAU/USD, Forex, indices, DXY, taux et crypto.",
        ),
    ]
    card_html = "\n".join(
        f"""            <article class="pulse-feature-card">
                <span>0{index}</span>
                <h2 data-i18n="{title_key}">{escape(title)}</h2>
                <p data-i18n="{copy_key}">{escape(copy)}</p>
            </article>"""
        for index, (title_key, title, copy_key, copy) in enumerate(pulse_cards, start=1)
    )
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title data-i18n="pulse_page_title">Market Pulse - Analyse marché du jour - XAUTERMINAL</title>
    <meta name="description" content="Market Pulse XAUTERMINAL synthétise le contexte macro, les actifs à surveiller, les news importantes et le calendrier économique avant une session de trading." data-i18n-content="pulse_page_description">
    <link rel="canonical" href="{canonical}">
    <meta name="robots" content="index,follow">
    <meta property="og:type" content="website">
    <meta property="og:site_name" content="XAUTERMINAL">
    <meta property="og:title" content="Market Pulse - Analyse marché du jour - XAUTERMINAL" data-i18n-content="pulse_page_title">
    <meta property="og:description" content="Une synthèse claire du contexte macro, des news, du calendrier et des actifs à surveiller avant d'ouvrir le terminal." data-i18n-content="pulse_page_description">
    <meta property="og:url" content="{canonical}">
    <meta property="og:image" content="{absolute_url('/static/icon-192x192.png')}">
    <meta name="twitter:card" content="summary">
{FAVICON_LINKS}
    <link rel="stylesheet" href="/static/styles.css">
    <script type="application/ld+json">{structured_data}</script>
</head>
<body class="legal-body">
    <header class="landing-nav">
        <a class="landing-brand" href="/" aria-label="XAUTERMINAL">
            {BRAND_MARKUP}
        </a>
        <nav class="landing-nav-actions" aria-label="Navigation principale">
            <a href="/#features" data-i18n="nav_tools">Outils</a>
            <a href="/marches" data-i18n="nav_markets">Marchés</a>
            <a href="/guides" data-i18n="nav_guides">Guides</a>
            <a href="/#pricing" data-i18n="nav_pricing">Formules</a>
            <a href="/support" data-i18n="nav_support">Support</a>
            <a href="/terminal" data-i18n="nav_terminal">Ouvrir le terminal</a>
            <button type="button" class="landing-lang" data-lang-toggle>EN</button>
        </nav>
    </header>

    <main class="legal-page market-pulse-page">
        <section class="pulse-hero">
            <div class="pulse-hero-copy">
                <div class="landing-kicker" data-i18n="pulse_page_kicker">MARKET PULSE</div>
                <h1 data-i18n="pulse_page_h1">Le briefing de marché avant d'ouvrir le terminal</h1>
                <p data-i18n="pulse_page_intro">Market Pulse rassemble la lecture macro essentielle: calendrier du jour, news qui comptent, actifs à surveiller, niveau de risque et biais de contexte. L'objectif est simple: savoir où regarder avant de prendre une décision.</p>
                <div class="pulse-live-note">
                    <span data-i18n="pulse_live_updated">Mis à jour</span>
                    <strong>{generated_at}</strong>
                </div>
                <div class="landing-actions">
                    <a class="resource-cta" href="/#pricing" data-i18n="pulse_page_trial">Tester XAUTERMINAL</a>
                    <a class="resource-link-button" href="/terminal" data-i18n="nav_terminal">Ouvrir le terminal</a>
                </div>
            </div>
            <aside class="pulse-board" aria-label="Aperçu Market Pulse">
                <div class="pulse-board-top">
                    <span data-i18n="pulse_board_today">AUJOURD'HUI</span>
                    <strong>{risk_label}</strong>
                </div>
                <div class="pulse-score">
                    <span>{risk_score}</span>
                    <p>{pulse_headline}</p>
                </div>
                <div class="pulse-mini-grid">
                    <div>
                        <span>XAU/USD</span>
                        <strong>{pulse_action}</strong>
                    </div>
                    <div>
                        <span>BIAS</span>
                        <strong>{pulse_bias}</strong>
                    </div>
                    <div>
                        <span data-i18n="pulse_board_news_label">News</span>
                        <strong>{len(news_items)}</strong>
                    </div>
                    <div>
                        <span data-i18n="pulse_calendar_label">Calendrier</span>
                        <strong>{len(calendar_items)}</strong>
                    </div>
                </div>
            </aside>
        </section>

        <section class="pulse-live-grid">
            <article class="pulse-live-panel">
                <div class="pulse-live-head">
                    <span data-i18n="pulse_live_news_kicker">NEWS LIVE</span>
                    <strong data-i18n="pulse_live_news_title">Titres importants récents</strong>
                </div>
{news_html}
            </article>
            <article class="pulse-live-panel">
                <div class="pulse-live-head">
                    <span data-i18n="pulse_live_calendar_kicker">CALENDRIER</span>
                    <strong data-i18n="pulse_live_calendar_title">Événements à venir</strong>
                </div>
{calendar_html}
                <p class="pulse-locked-note">{locked_note}</p>
            </article>
        </section>

        <section class="pulse-feature-grid">
{card_html}
        </section>

        <section class="pulse-workflow">
            <div>
                <div class="landing-kicker" data-i18n="pulse_workflow_kicker">ROUTINE</div>
                <h2 data-i18n="pulse_workflow_title">Une routine en quatre lectures</h2>
                <p data-i18n="pulse_workflow_copy">Les meilleurs terminaux ne montrent pas seulement des données: ils aident à décider quelles données méritent ton attention. Market Pulse sert de première couche avant le charting.</p>
            </div>
            <ol>
                <li><strong data-i18n="pulse_step1_title">Calendrier</strong><span data-i18n="pulse_step1_copy">Repérer les horaires à risque et les publications capables de déplacer le dollar, les taux ou les indices.</span></li>
                <li><strong data-i18n="pulse_step2_title">News</strong><span data-i18n="pulse_step2_copy">Filtrer les titres vraiment liés au thème dominant de la séance.</span></li>
                <li><strong data-i18n="pulse_step3_title">Drivers</strong><span data-i18n="pulse_step3_copy">Comparer dollar, rendements, sentiment de risque et momentum du prix.</span></li>
                <li><strong data-i18n="pulse_step4_title">Plan</strong><span data-i18n="pulse_step4_copy">Passer au terminal avec une watchlist claire, pas avec dix onglets ouverts au hasard.</span></li>
            </ol>
        </section>

        <section class="pulse-assets">
            <div class="landing-section-head">
                <div class="landing-kicker" data-i18n="pulse_assets_kicker">RADAR MARCHÉS</div>
                <h2 data-i18n="pulse_assets_title">Les marchés qui méritent une lecture dédiée</h2>
            </div>
            <p class="pulse-public-summary">{pulse_summary}</p>
            <div class="pulse-asset-grid">
{asset_html}
            </div>
        </section>

        <section class="pulse-assets">
            <div class="landing-section-head">
                <div class="landing-kicker" data-i18n="pulse_drivers_kicker">DRIVERS PUBLICS</div>
                <h2 data-i18n="pulse_drivers_title">Ce qui influence le contexte</h2>
            </div>
            <div class="pulse-asset-grid">
{driver_html}
            </div>
        </section>

        <section class="legal-contact article-cta">
            <h2 data-i18n="pulse_final_title">Pourquoi ajouter Market Pulse à XAUTERMINAL ?</h2>
            <p data-i18n="pulse_final_copy">Parce que le vrai problème d'un trader n'est pas seulement de trouver des données, mais de les hiérarchiser. Market Pulse donne une porte d'entrée claire avant le terminal complet, les graphiques et le Bias Desk.</p>
            <div class="landing-actions">
                <a class="resource-cta" href="/#pricing" data-i18n="pulse_page_trial">Tester XAUTERMINAL</a>
                <a class="resource-link-button" href="/guides" data-i18n="nav_guides">Guides</a>
            </div>
        </section>
    </main>
{PUBLIC_FOOTER}
    <script src="/static/landing.js"></script>
</body>
</html>"""


def market_lang_script() -> str:
    return """    <script>
    (function () {
        const copy = window.XT_MARKET_COPY || {};
        function applyMarketLanguage() {
            const lang = window.XT_INITIAL_LANG || localStorage.getItem('xt_lang') || 'fr';
            const current = copy[lang] || copy.en || copy.fr || {};
            document.querySelectorAll('[data-market-i18n]').forEach((el) => {
                const key = el.dataset.marketI18n;
                if (current[key] !== undefined) el.textContent = current[key];
            });
            document.querySelectorAll('[data-market-content]').forEach((el) => {
                const key = el.dataset.marketContent;
                if (current[key] !== undefined) el.setAttribute('content', current[key]);
            });
            const title = document.querySelector('title[data-market-i18n]');
            if (title && current[title.dataset.marketI18n]) title.textContent = current[title.dataset.marketI18n];
        }
        applyMarketLanguage();
        document.querySelectorAll('[data-lang-toggle]').forEach((button) => {
            button.addEventListener('click', () => window.setTimeout(applyMarketLanguage, 0));
        });
    })();
    </script>"""


def markets_index_page() -> str:
    canonical = absolute_url("/marches")
    title = "Marchés Forex les plus tradés - XAUTERMINAL"
    description = "Radar des paires Forex les plus tradées au monde: EUR/USD, USD/JPY, GBP/USD, USD/CNY, USD/CAD, AUD/USD, USD/CHF et principaux crosses."
    cards = "\n".join(
        f"""            <article class="market-card">
                <div class="market-card-top">
                    <span>#{pair["rank"]:02d}</span>
                    <em>{escape(pair["share"])}</em>
                </div>
                <h2>{escape(pair["pair"])}</h2>
                <strong data-market-i18n="{pair["slug"]}_name">{escape(pair["fr"]["name"])}</strong>
                <p data-market-i18n="{pair["slug"]}_headline">{escape(pair["fr"]["headline"])}</p>
                <div class="market-card-actions">
                    <a class="resource-cta" href="/marches/{escape(pair["slug"], quote=True)}" data-market-i18n="read_market">Lire</a>
                    <a class="resource-link-button" href="/terminal?symbol={escape(pair["tv_symbol"], quote=True)}" data-market-i18n="open_terminal">Terminal</a>
                </div>
            </article>"""
        for pair in FX_MARKET_PAIRS
    )
    copy = {
        "fr": {
            "page_title": title,
            "page_description": description,
            "kicker": "MARCHÉS FOREX",
            "h1": "Les paires Forex les plus tradées au monde",
            "intro": "Ce radar regroupe les paires de devises les plus liquides et les plus surveillées par les traders. Chaque page explique le rôle de la paire, les drivers à suivre et comment XAUTERMINAL peut aider à la replacer dans un contexte macro.",
            "source_note": "Classement indicatif construit autour des données BIS 2025 et des paires les plus liquides. Les pourcentages sont des ordres de grandeur publics, pas un flux de volume temps réel.",
            "daily_volume": "9.6T$ / jour",
            "read_market": "Lire",
            "open_terminal": "Terminal",
            "why_title": "Pourquoi créer des pages par paire ?",
            "why_copy": "Les meilleurs terminaux organisent le marché par instrument: graphique, news, calendrier, drivers et contexte. La page publique donne la carte; le terminal donne la lecture complète.",
            "cta_title": "Passer du radar public au terminal complet",
            "cta_copy": "Dans le terminal, les paires peuvent être ouvertes avec le charting, les news, le calendrier, la watchlist et le Bias Desk adapté au symbole.",
        },
        "en": {
            "page_title": "Most traded Forex markets - XAUTERMINAL",
            "page_description": "Radar of the world's most traded Forex pairs: EUR/USD, USD/JPY, GBP/USD, USD/CNY, USD/CAD, AUD/USD, USD/CHF and major crosses.",
            "kicker": "FOREX MARKETS",
            "h1": "The most traded Forex pairs in the world",
            "intro": "This radar groups the most liquid currency pairs watched by traders. Each page explains the role of the pair, drivers to monitor and how XAUTERMINAL helps place it in macro context.",
            "source_note": "Indicative ranking built around BIS 2025 data and the most liquid pairs. Percentages are public orders of magnitude, not a real-time volume feed.",
            "daily_volume": "$9.6T / day",
            "read_market": "Read",
            "open_terminal": "Terminal",
            "why_title": "Why create pages by pair?",
            "why_copy": "The best terminals organize markets by instrument: chart, news, calendar, drivers and context. The public page gives the map; the terminal gives the complete read.",
            "cta_title": "Move from public radar to the full terminal",
            "cta_copy": "Inside the terminal, pairs can be opened with charting, news, calendar, watchlist and symbol-adapted Bias Desk.",
        },
    }
    for pair in FX_MARKET_PAIRS:
        copy["fr"][f"{pair['slug']}_name"] = pair["fr"]["name"]
        copy["fr"][f"{pair['slug']}_headline"] = pair["fr"]["headline"]
        copy["en"][f"{pair['slug']}_name"] = pair["en"]["name"]
        copy["en"][f"{pair['slug']}_headline"] = pair["en"]["headline"]
    structured_data = json.dumps({
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": title,
        "description": description,
        "url": canonical,
        "hasPart": [
            {
                "@type": "WebPage",
                "name": f"{pair['pair']} - XAUTERMINAL",
                "url": absolute_url(f"/marches/{pair['slug']}"),
            }
            for pair in FX_MARKET_PAIRS
        ],
    }, ensure_ascii=False)
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title data-market-i18n="page_title">{escape(title)}</title>
    <meta name="description" content="{escape(description, quote=True)}" data-market-content="page_description">
    <link rel="canonical" href="{canonical}">
    <meta name="robots" content="index,follow">
    <meta property="og:type" content="website">
    <meta property="og:site_name" content="XAUTERMINAL">
    <meta property="og:title" content="{escape(title, quote=True)}" data-market-content="page_title">
    <meta property="og:description" content="{escape(description, quote=True)}" data-market-content="page_description">
    <meta property="og:url" content="{canonical}">
    <meta property="og:image" content="{absolute_url('/static/icon-192x192.png')}">
    <meta name="twitter:card" content="summary">
{FAVICON_LINKS}
    <link rel="stylesheet" href="/static/styles.css">
    <script type="application/ld+json">{structured_data}</script>
</head>
<body class="legal-body">
    <header class="landing-nav">
        <a class="landing-brand" href="/" aria-label="XAUTERMINAL">
            {BRAND_MARKUP}
        </a>
        <nav class="landing-nav-actions" aria-label="Navigation principale">
            <a href="/market-pulse" data-i18n="nav_pulse">Market Pulse</a>
            <a href="/guides" data-i18n="nav_guides">Guides</a>
            <a href="/#pricing" data-i18n="nav_pricing">Formules</a>
            <a href="/support" data-i18n="nav_support">Support</a>
            <a href="/terminal" data-i18n="nav_terminal">Ouvrir le terminal</a>
            <button type="button" class="landing-lang" data-lang-toggle>EN</button>
        </nav>
    </header>
    <main class="legal-page markets-page">
        <section class="markets-hero">
            <div>
                <div class="landing-kicker" data-market-i18n="kicker">MARCHÉS FOREX</div>
                <h1 data-market-i18n="h1">Les paires Forex les plus tradées au monde</h1>
                <p data-market-i18n="intro">Ce radar regroupe les paires de devises les plus liquides et les plus surveillées par les traders. Chaque page explique le rôle de la paire, les drivers à suivre et comment XAUTERMINAL peut aider à la replacer dans un contexte macro.</p>
                <div class="landing-actions">
                    <a class="resource-cta" href="/#pricing" data-i18n="footer_trial">Démarrer l'essai</a>
                    <a class="resource-link-button" href="/market-pulse" data-i18n="nav_pulse">Market Pulse</a>
                </div>
            </div>
            <aside class="markets-source-panel">
                <span>BIS 2025</span>
                <strong data-market-i18n="daily_volume">9.6T$ / jour</strong>
                <p data-market-i18n="source_note">Classement indicatif construit autour des données BIS 2025 et des paires les plus liquides. Les pourcentages sont des ordres de grandeur publics, pas un flux de volume temps réel.</p>
            </aside>
        </section>
        <section class="market-grid">
{cards}
        </section>
        <section class="pulse-workflow markets-explain">
            <div>
                <div class="landing-kicker">XAUTERMINAL</div>
                <h2 data-market-i18n="why_title">Pourquoi créer des pages par paire ?</h2>
                <p data-market-i18n="why_copy">Les meilleurs terminaux organisent le marché par instrument: graphique, news, calendrier, drivers et contexte. La page publique donne la carte; le terminal donne la lecture complète.</p>
            </div>
            <div>
                <h2 data-market-i18n="cta_title">Passer du radar public au terminal complet</h2>
                <p data-market-i18n="cta_copy">Dans le terminal, les paires peuvent être ouvertes avec le charting, les news, le calendrier, la watchlist et le Bias Desk adapté au symbole.</p>
                <div class="landing-actions">
                    <a class="resource-cta" href="/#pricing" data-i18n="footer_trial">Démarrer l'essai</a>
                    <a class="resource-link-button" href="/terminal" data-i18n="nav_terminal">Ouvrir le terminal</a>
                </div>
            </div>
        </section>
    </main>
{PUBLIC_FOOTER}
    <script>window.XT_MARKET_COPY = {json.dumps(copy, ensure_ascii=False)};</script>
    <script src="/static/landing.js"></script>
{market_lang_script()}
</body>
</html>"""


def market_pair_page(slug: str) -> str:
    pair = FX_MARKET_BY_SLUG[slug]
    canonical = absolute_url(f"/marches/{slug}")
    fr = pair["fr"]
    en = pair["en"]
    title = f"{pair['pair']} - Analyse de marché Forex - XAUTERMINAL"
    description = f"Comprendre {pair['pair']}: rôle de la paire, principaux drivers macro, news, calendrier et lecture dans le terminal XAUTERMINAL."
    driver_tags = "\n".join(
        f'<span data-market-i18n="driver_{index}">{escape(driver)}</span>'
        for index, driver in enumerate(fr["drivers"])
    )
    related_cards = "\n".join(
        f"""                <a href="/marches/{escape(item["slug"], quote=True)}">{escape(item["pair"])}</a>"""
        for item in FX_MARKET_PAIRS
        if item["slug"] != slug
    )
    copy = {
        "fr": {
            "page_title": title,
            "page_description": description,
            "kicker": "MARCHÉ FOREX",
            "h1": f"{pair['pair']}: {fr['headline']}",
            "intro": fr["intro"],
            "rank_label": "Rang volume FX",
            "share_label": "Part indicative",
            "role_title": "Pourquoi cette paire compte",
            "role_copy": fr["role"],
            "drivers_title": "Drivers à surveiller",
            "terminal_title": "Lecture dans XAUTERMINAL",
            "terminal_copy": fr["terminal"],
            "public_limit_title": "Ce que la page publique ne donne pas",
            "public_limit_copy": "La page explique la logique de marché, mais les données live complètes, le Bias Desk, les news filtrées et le calendrier détaillé restent réservés au terminal.",
            "related_title": "Autres paires liquides",
            "all_markets": "Voir tous les marchés",
            "open_terminal": "Ouvrir dans le terminal",
        },
        "en": {
            "page_title": f"{pair['pair']} - Forex market analysis - XAUTERMINAL",
            "page_description": f"Understand {pair['pair']}: pair role, key macro drivers, news, calendar and XAUTERMINAL terminal read.",
            "kicker": "FOREX MARKET",
            "h1": f"{pair['pair']}: {en['headline']}",
            "intro": en["intro"],
            "rank_label": "FX volume rank",
            "share_label": "Indicative share",
            "role_title": "Why this pair matters",
            "role_copy": en["role"],
            "drivers_title": "Drivers to watch",
            "terminal_title": "Read in XAUTERMINAL",
            "terminal_copy": en["terminal"],
            "public_limit_title": "What the public page does not provide",
            "public_limit_copy": "The page explains the market logic, but complete live data, Bias Desk, filtered news and detailed calendar remain reserved for the terminal.",
            "related_title": "Other liquid pairs",
            "all_markets": "View all markets",
            "open_terminal": "Open in terminal",
        },
    }
    for index, driver in enumerate(fr["drivers"]):
        copy["fr"][f"driver_{index}"] = driver
    for index, driver in enumerate(en["drivers"]):
        copy["en"][f"driver_{index}"] = driver
    structured_data = json.dumps({
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": title,
        "description": description,
        "url": canonical,
        "about": {
            "@type": "FinancialProduct",
            "name": pair["pair"],
            "description": fr["role"],
        },
        "isPartOf": {
            "@type": "WebSite",
            "name": "XAUTERMINAL",
            "url": APP_BASE_URL,
        },
    }, ensure_ascii=False)
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title data-market-i18n="page_title">{escape(title)}</title>
    <meta name="description" content="{escape(description, quote=True)}" data-market-content="page_description">
    <link rel="canonical" href="{canonical}">
    <meta name="robots" content="index,follow">
    <meta property="og:type" content="article">
    <meta property="og:site_name" content="XAUTERMINAL">
    <meta property="og:title" content="{escape(title, quote=True)}" data-market-content="page_title">
    <meta property="og:description" content="{escape(description, quote=True)}" data-market-content="page_description">
    <meta property="og:url" content="{canonical}">
    <meta property="og:image" content="{absolute_url('/static/icon-192x192.png')}">
    <meta name="twitter:card" content="summary">
{FAVICON_LINKS}
    <link rel="stylesheet" href="/static/styles.css">
    <script type="application/ld+json">{structured_data}</script>
</head>
<body class="legal-body">
    <header class="landing-nav">
        <a class="landing-brand" href="/" aria-label="XAUTERMINAL">
            {BRAND_MARKUP}
        </a>
        <nav class="landing-nav-actions" aria-label="Navigation principale">
            <a href="/marches" data-i18n="nav_markets">Marchés</a>
            <a href="/market-pulse" data-i18n="nav_pulse">Market Pulse</a>
            <a href="/guides" data-i18n="nav_guides">Guides</a>
            <a href="/#pricing" data-i18n="nav_pricing">Formules</a>
            <a href="/support" data-i18n="nav_support">Support</a>
            <a href="/terminal" data-i18n="nav_terminal">Ouvrir le terminal</a>
            <button type="button" class="landing-lang" data-lang-toggle>EN</button>
        </nav>
    </header>
    <main class="legal-page markets-page">
        <section class="markets-hero market-detail-hero">
            <div>
                <div class="landing-kicker" data-market-i18n="kicker">MARCHÉ FOREX</div>
                <h1 data-market-i18n="h1">{escape(pair["pair"])}: {escape(fr["headline"])}</h1>
                <p data-market-i18n="intro">{escape(fr["intro"])}</p>
                <div class="landing-actions">
                    <a class="resource-cta" href="/terminal?symbol={escape(pair["tv_symbol"], quote=True)}" data-market-i18n="open_terminal">Ouvrir dans le terminal</a>
                    <a class="resource-link-button" href="/marches" data-market-i18n="all_markets">Voir tous les marchés</a>
                </div>
            </div>
            <aside class="markets-source-panel">
                <span>{escape(pair["pair"])}</span>
                <strong>#{pair["rank"]:02d}</strong>
                <p><span data-market-i18n="rank_label">Rang volume FX</span> · <span data-market-i18n="share_label">Part indicative</span> {escape(pair["share"])}</p>
            </aside>
        </section>
        <section class="market-detail-grid">
            <article class="market-detail-card">
                <span>01</span>
                <h2 data-market-i18n="role_title">Pourquoi cette paire compte</h2>
                <p data-market-i18n="role_copy">{escape(fr["role"])}</p>
            </article>
            <article class="market-detail-card">
                <span>02</span>
                <h2 data-market-i18n="drivers_title">Drivers à surveiller</h2>
                <div class="market-driver-tags">{driver_tags}</div>
            </article>
            <article class="market-detail-card featured">
                <span>03</span>
                <h2 data-market-i18n="terminal_title">Lecture dans XAUTERMINAL</h2>
                <p data-market-i18n="terminal_copy">{escape(fr["terminal"])}</p>
                <a class="resource-cta" href="/#pricing" data-i18n="footer_trial">Démarrer l'essai</a>
            </article>
            <article class="market-detail-card">
                <span>04</span>
                <h2 data-market-i18n="public_limit_title">Ce que la page publique ne donne pas</h2>
                <p data-market-i18n="public_limit_copy">La page explique la logique de marché, mais les données live complètes, le Bias Desk, les news filtrées et le calendrier détaillé restent réservés au terminal.</p>
            </article>
        </section>
        <section class="pulse-assets">
            <div class="landing-section-head">
                <div class="landing-kicker" data-market-i18n="related_title">Autres paires liquides</div>
                <h2>{escape(pair["pair"])} / Forex radar</h2>
            </div>
            <div class="market-related-links">
{related_cards}
            </div>
        </section>
    </main>
{PUBLIC_FOOTER}
    <script>window.XT_MARKET_COPY = {json.dumps(copy, ensure_ascii=False)};</script>
    <script src="/static/landing.js"></script>
{market_lang_script()}
</body>
</html>"""


def support_page() -> str:
    canonical = absolute_url("/support")
    email = LEGAL_CONTACT_EMAIL
    structured_data = json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "ContactPage",
            "name": "Support XAUTERMINAL",
            "description": "Aide XAUTERMINAL pour les comptes, codes email, paiements Stripe, abonnements, accès au terminal et sécurité.",
            "url": canonical,
            "publisher": {
                "@type": "Organization",
                "name": LEGAL_BUSINESS_NAME,
                "url": APP_BASE_URL,
                "logo": absolute_url("/static/icon-192x192.png"),
                "contactPoint": {
                    "@type": "ContactPoint",
                    "email": email,
                    "contactType": "customer support",
                    "availableLanguage": ["fr", "en"],
                },
            },
        },
        ensure_ascii=False,
    )
    cards = [
        ("support_card_code_title", "support_card_code_copy"),
        ("support_card_paid_title", "support_card_paid_copy"),
        ("support_card_password_title", "support_card_password_copy"),
        ("support_card_subscription_title", "support_card_subscription_copy"),
        ("support_card_terminal_title", "support_card_terminal_copy"),
        ("support_card_security_title", "support_card_security_copy"),
    ]
    card_html = "\n".join(
        f"""            <article class="support-card">
                <h2 data-i18n="{title_key}">{title_key}</h2>
                <p data-i18n="{copy_key}">{copy_key}</p>
            </article>"""
        for title_key, copy_key in cards
    )
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title data-i18n="support_title">Support XAUTERMINAL</title>
    <meta name="description" content="Aide XAUTERMINAL pour les comptes, codes email, paiements Stripe, abonnements, accès au terminal et sécurité." data-i18n-content="support_description">
    <link rel="canonical" href="{canonical}">
    <meta name="robots" content="index,follow">
    <meta property="og:type" content="website">
    <meta property="og:site_name" content="XAUTERMINAL">
    <meta property="og:title" content="Support XAUTERMINAL" data-i18n-content="support_title">
    <meta property="og:description" content="Aide XAUTERMINAL pour les comptes, codes email, paiements Stripe, abonnements, accès au terminal et sécurité." data-i18n-content="support_description">
    <meta property="og:url" content="{canonical}">
    <meta property="og:image" content="{absolute_url('/static/icon-192x192.png')}">
    <meta name="twitter:card" content="summary">
{FAVICON_LINKS}
    <link rel="stylesheet" href="/static/styles.css">
    <script type="application/ld+json">{structured_data}</script>
</head>
<body class="legal-body">
    <header class="landing-nav">
        <a class="landing-brand" href="/" aria-label="XAUTERMINAL">
            {BRAND_MARKUP}
        </a>
        <nav class="landing-nav-actions" aria-label="Navigation support">
            <a href="/marches" data-i18n="nav_markets">Marchés</a>
            <a href="/market-pulse" data-i18n="nav_pulse">Market Pulse</a>
            <a href="/guides" data-i18n="nav_guides">Guides</a>
            <a href="/#pricing" data-i18n="nav_pricing">Formules</a>
            <a href="/account" data-i18n="nav_account">Mon compte</a>
            <button type="button" class="landing-lang" data-lang-toggle>EN</button>
        </nav>
    </header>

    <main class="legal-page support-page">
        <div class="landing-kicker" data-i18n="support_kicker">SUPPORT</div>
        <h1 data-i18n="support_h1">Aide et support XAUTERMINAL</h1>
        <p data-i18n="support_intro">Retrouve les réponses aux situations les plus fréquentes: validation email, accès au terminal, paiement Stripe, abonnement, mot de passe et sécurité du compte.</p>

        <section class="support-quick-actions" aria-label="Actions rapides">
            <a class="resource-cta" href="/account" data-i18n="support_action_account">Ouvrir mon compte</a>
            <a class="resource-link-button" href="/#pricing" data-i18n="support_action_plans">Voir les formules</a>
            <a class="resource-link-button" href="/reset-password" data-i18n="support_action_password">Réinitialiser mon mot de passe</a>
        </section>

        <section class="support-grid" aria-label="Questions fréquentes">
{card_html}
        </section>

        <section class="support-process">
            <h2 data-i18n="support_process_title">Avant de contacter le support</h2>
            <ol>
                <li data-i18n="support_process_1">Vérifie que ton email est bien confirmé avec le dernier code reçu.</li>
                <li data-i18n="support_process_2">Si tu as payé, reconnecte-toi puis ouvre ton espace Mon compte pour relancer la synchronisation automatique.</li>
                <li data-i18n="support_process_3">Si l'accès reste bloqué, contacte le support avec ton email de compte et, si possible, l'heure du paiement Stripe.</li>
            </ol>
        </section>

        <section class="legal-contact">
            <h2 data-i18n="support_contact_title">Contacter XAUTERMINAL</h2>
            <p><span data-i18n="support_contact_copy">Pour une demande compte, paiement ou accès terminal, écris-nous à</span> <a href="mailto:{email}">{email}</a>.</p>
        </section>
    </main>

{PUBLIC_FOOTER}
    <script src="/static/landing.js"></script>
</body>
</html>"""


LEGAL_FR_COPY = {
    "terms_section1_title": "Objet du service",
    "terms_section1": "XAUTERMINAL propose un terminal web d'information macro et marché permettant de consulter des news, un calendrier économique, des graphiques, des watchlists, des widgets de prix et des outils de lecture de contexte. Le service est fourni comme outil d'aide à l'organisation et à l'analyse personnelle.",
    "terms_section2_title": "Accès au service",
    "terms_section2": "L'accès complet peut être soumis à la création d'un compte, à une période d'essai, à un abonnement ou à une offre lifetime. L'utilisateur s'engage à fournir des informations exactes et à préserver la confidentialité de ses identifiants.",
    "terms_section3_title": "Essai gratuit et abonnements",
    "terms_section3": "Les formules mensuelle et annuelle peuvent inclure un essai gratuit de 7 jours. Selon la configuration Stripe, une carte bancaire peut être demandée au démarrage de l'essai afin de préparer le renouvellement. À l'issue de l'essai, l'abonnement choisi démarre automatiquement si le paiement est validé. L'abonnement mensuel est souscrit pour une période d'un mois renouvelable. L'abonnement annuel est souscrit pour une période d'un an renouvelable. L'offre lifetime correspond à un paiement unique donnant accès au service tant que celui-ci est exploité.",
    "terms_section4_title": "Paiement",
    "terms_section4": "Les paiements sont traités par Stripe. XAUTERMINAL ne stocke pas les numéros de carte bancaire. Sauf obligation légale contraire, toute période d'abonnement commencée et payée est due et non remboursable: un mois payé reste dû pour le mois en cours, une année payée reste due pour l'année en cours. La résiliation met fin au renouvellement automatique à l'échéance de la période en cours, sans remboursement prorata temporis.",
    "terms_section5_title": "Utilisation acceptable",
    "terms_section5": "L'utilisateur s'engage à ne pas perturber le service, contourner les restrictions d'accès, partager un compte de manière abusive, extraire massivement les données ou utiliser le service à des fins illicites.",
    "terms_section6_title": "Disponibilité",
    "terms_section6": "Le service dépend de fournisseurs tiers, notamment hébergement, données de marché, flux d'actualité, calendrier économique, graphiques et paiement. Des interruptions, retards, erreurs ou indisponibilités peuvent survenir.",
    "terms_section7_title": "Responsabilité",
    "terms_section7": "XAUTERMINAL ne garantit pas l'exactitude, l'exhaustivité, l'actualité ou la continuité des données affichées. L'utilisateur reste seul responsable de ses décisions, notamment financières, et de sa gestion du risque.",
    "terms_section8_title": "Rétractation",
    "terms_section8": "Lorsque la loi accorde un droit de rétractation, l'utilisateur dispose en principe d'un délai de 14 jours pour l'exercer à compter de la conclusion du contrat. XAUTERMINAL étant un service numérique accessible immédiatement, l'utilisateur demande expressément l'exécution immédiate du service dès la souscription Stripe, y compris pendant l'essai gratuit, et reconnaît que cette exécution immédiate peut entraîner la perte du droit de rétractation lorsque les conditions légales applicables sont réunies. Pendant l'essai gratuit, l'utilisateur peut annuler avant le premier paiement depuis Stripe.",
    "terms_section9_title": "Résiliation",
    "terms_section9": "L'utilisateur peut demander la résiliation de son abonnement depuis son espace compte ou le portail Stripe. La résiliation d'un abonnement mensuel ou annuel prend effet à la fin de la période de facturation en cours et n'annule pas les sommes déjà dues pour cette période.",
    "terms_section10_title": "Modification du service",
    "terms_section10": "Les fonctionnalités, tarifs, offres, sources de données et conditions peuvent évoluer afin d'améliorer le produit, corriger des erreurs ou tenir compte de contraintes techniques ou commerciales.",
    "terms_section11_title": "Archivage et preuve",
    "terms_section11": "Les informations liées au compte, aux paiements, aux abonnements, aux confirmations email et à l'acceptation des conditions peuvent être conservées afin d'assurer la preuve de la relation contractuelle, gérer le support, prévenir la fraude et respecter les obligations légales.",
    "terms_section12_title": "Réclamation",
    "terms_section12": "Pour toute réclamation, l'utilisateur doit contacter XAUTERMINAL par email en indiquant l'adresse de compte concernée, le problème rencontré et les justificatifs utiles. XAUTERMINAL s'efforce de répondre dans un délai raisonnable.",
    "privacy_section1_title": "Données collectées",
    "privacy_section1": "XAUTERMINAL peut collecter l'adresse email, le mot de passe chiffré, les informations de profil renseignées volontairement comme prénom, nom et adresse, les préférences de terminal, l'état d'abonnement, les identifiants Stripe nécessaires au suivi du paiement et des données techniques liées à l'utilisation du service.",
    "privacy_section2_title": "Finalités",
    "privacy_section2": "Ces données servent à créer et sécuriser le compte, gérer l'accès au terminal, synchroniser les préférences, traiter les abonnements, améliorer le produit et assurer le support utilisateur.",
    "privacy_section3_title": "Paiements",
    "privacy_section3": "Les données de paiement sont traitées par Stripe. XAUTERMINAL conserve uniquement les références techniques utiles au suivi du compte, comme l'identifiant client, l'abonnement, le prix sélectionné ou le statut de paiement.",
    "privacy_section4_title": "Cookies et sessions",
    "privacy_section4": "Le service utilise un cookie de session afin de maintenir la connexion au compte. Des préférences peuvent également être conservées localement dans le navigateur pour personnaliser l'expérience.",
    "privacy_section5_title": "Prestataires",
    "privacy_section5": "Le service peut s'appuyer sur des prestataires techniques comme Render pour l'hébergement, Stripe pour le paiement, Financial Modeling Prep, Yahoo Finance, TradingView ou des flux RSS tiers pour les données et l'affichage.",
    "privacy_section6_title": "Durée de conservation",
    "privacy_section6": "Les données de compte sont conservées tant que le compte existe ou tant que cela est nécessaire pour fournir le service, respecter des obligations légales, gérer un litige ou assurer la sécurité.",
    "privacy_section7_title": "Droits utilisateur",
    "privacy_section7": "L'utilisateur peut demander l'accès, la correction ou la suppression de ses données en contactant l'adresse indiquée sur cette page. Certaines données peuvent être conservées si une obligation légale ou technique l'impose.",
    "privacy_section8_title": "Sécurité",
    "privacy_section8": "XAUTERMINAL applique des mesures raisonnables pour protéger les comptes et les données. Aucun système n'étant infaillible, l'utilisateur doit choisir un mot de passe robuste et éviter de le réutiliser.",
    "privacy_section9_title": "Responsable du traitement et bases légales",
    "privacy_section9": "Le responsable du traitement est l'éditeur indiqué dans les mentions légales. Les traitements reposent selon les cas sur l'exécution du contrat, l'intérêt légitime de sécurisation et d'amélioration du service, le respect d'obligations légales ou le consentement lorsque celui-ci est requis.",
    "privacy_section10_title": "Droits RGPD et CNIL",
    "privacy_section10": "L'utilisateur peut demander l'accès, la rectification, l'effacement, la limitation, l'opposition au traitement ou la portabilité de ses données lorsque ces droits sont applicables. Il peut également introduire une réclamation auprès de la CNIL.",
    "privacy_section11_title": "Transferts et prestataires hors UE",
    "privacy_section11": "Certains prestataires techniques, de paiement, d'email, de données de marché ou d'affichage peuvent traiter des données hors Union européenne. Lorsque cela est nécessaire, XAUTERMINAL s'appuie sur les garanties proposées par ces prestataires, notamment leurs mécanismes contractuels et de conformité.",
    "privacy_section12_title": "Données obligatoires ou facultatives",
    "privacy_section12": "L'email, le mot de passe et les informations de paiement nécessaires via Stripe sont requis pour créer un compte et fournir l'accès. Les informations de profil complémentaires sont facultatives, sauf lorsqu'elles sont nécessaires à la facturation, au support ou à une obligation légale.",
    "risk_section1_title": "Information uniquement",
    "risk_section1": "XAUTERMINAL fournit des informations de marché, des outils de visualisation, des classements, des alertes et des lectures de contexte. Le service ne constitue pas un conseil en investissement, une recommandation personnalisée, une gestion de portefeuille, ou une incitation à acheter ou vendre un instrument financier.",
    "risk_section2_title": "Risque de perte",
    "risk_section2": "Le trading, les CFD, le Forex, les cryptomonnaies, les actions, les indices, les matières premières et autres instruments financiers comportent un risque élevé de perte. Les performances passées ne préjugent pas des performances futures.",
    "risk_section3_title": "Données tierces",
    "risk_section3": "Les prix, news, calendriers économiques, impacts, prévisions, données actual/forecast/previous et graphiques peuvent provenir de fournisseurs tiers. Ces informations peuvent être retardées, erronées, incomplètes ou indisponibles.",
    "risk_section4_title": "Bias Desk",
    "risk_section4": "Le Bias Desk et les indicateurs associés sont des outils de lecture mécanique et contextuelle. Ils ne doivent pas être interprétés comme des signaux automatiques ou comme une garantie de résultat.",
    "risk_section5_title": "Responsabilité de l'utilisateur",
    "risk_section5": "Chaque utilisateur doit effectuer ses propres vérifications, respecter son plan de trading, adapter la taille de ses positions et ne jamais engager de capitaux qu'il ne peut pas se permettre de perdre.",
    "risk_section6_title": "Aucune garantie",
    "risk_section6": "XAUTERMINAL ne garantit aucun gain, aucune précision parfaite des données, aucune disponibilité continue et aucune adéquation du service à une situation financière particulière.",
}


def legal_page(title_key: str, kicker_key: str, sections: list[tuple[str, str]]) -> str:
    meta = LEGAL_PAGE_META[title_key]
    business_name = LEGAL_BUSINESS_NAME
    email = LEGAL_CONTACT_EMAIL
    page_path = {
        "terms_title": "/terms",
        "privacy_title": "/privacy",
        "risk_title": "/risk-disclaimer",
    }[title_key]
    description_key = title_key.replace("_title", "_description")
    canonical = absolute_url(page_path)
    page_title = f'{meta["title"]} - {business_name}'
    escaped_description = escape(meta["description"], quote=True)
    structured_data = json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": meta["title"],
            "description": meta["description"],
            "url": canonical,
            "isPartOf": {
                "@type": "WebSite",
                "name": business_name,
                "url": APP_BASE_URL,
            },
            "publisher": {
                "@type": "Organization",
                "name": business_name,
                "url": APP_BASE_URL,
                "logo": absolute_url("/static/icon-192x192.png"),
            },
            "inLanguage": "fr-FR",
        },
        ensure_ascii=False,
    )
    section_html = "\n".join(
        f'<section><h2 data-i18n="{section_title_key}">{escape(LEGAL_FR_COPY.get(section_title_key, section_title_key))}</h2><p data-i18n="{section_content_key}">{escape(LEGAL_FR_COPY.get(section_content_key, section_content_key))}</p></section>'
        for section_title_key, section_content_key in sections
    )
    vat_line = f'<br><span data-i18n="legal_vat">TVA intracommunautaire</span> : {escape(LEGAL_VAT_ID)}' if LEGAL_VAT_ID else ""
    mediator_name = LEGAL_MEDIATOR_NAME or "Médiateur de la consommation à renseigner"
    mediator_url = LEGAL_MEDIATOR_URL or "https://www.economie.gouv.fr/mediation-conso"
    mediator_address = LEGAL_MEDIATOR_ADDRESS or "Coordonnées du médiateur à compléter après adhésion au dispositif choisi."
    terms_extra = ""
    if title_key == "terms_title":
        terms_extra = f"""
        <section>
            <h2 data-i18n="terms_mediation_title">Médiation de la consommation</h2>
            <p>
                <span data-i18n="terms_mediation_copy">Après une réclamation écrite préalable adressée à XAUTERMINAL restée sans solution satisfaisante, le consommateur peut saisir gratuitement le médiateur de la consommation compétent.</span><br>
                <span data-i18n="terms_mediation_name">Médiateur</span> : {escape(mediator_name)}<br>
                <span data-i18n="terms_mediation_site">Site</span> : <a href="{escape(mediator_url, quote=True)}" target="_blank" rel="noopener noreferrer">{escape(mediator_url)}</a><br>
                <span data-i18n="terms_mediation_address">Adresse</span> : {escape(mediator_address)}
            </p>
        </section>
        <section>
            <h2 data-i18n="terms_withdrawal_form_title">Formulaire type de rétractation</h2>
            <p data-i18n="terms_withdrawal_form_copy">Lorsque le droit de rétractation est applicable, l'utilisateur peut envoyer une demande claire par email à l'adresse de contact, en indiquant son nom, son email de compte, la formule concernée, la date de commande et la phrase: Je vous notifie par la présente ma rétractation du contrat portant sur le service XAUTERMINAL.</p>
        </section>
        """
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title data-i18n="{title_key}">{page_title}</title>
    <meta name="description" content="{escaped_description}" data-i18n-content="{description_key}">
    <link rel="canonical" href="{canonical}">
    <meta name="robots" content="index,follow">
    <meta property="og:type" content="website">
    <meta property="og:site_name" content="{business_name}">
    <meta property="og:title" content="{page_title}" data-i18n-content="{title_key}">
    <meta property="og:description" content="{escaped_description}" data-i18n-content="{description_key}">
    <meta property="og:url" content="{canonical}">
    <meta property="og:image" content="{absolute_url('/static/icon-192x192.png')}">
    <meta name="twitter:card" content="summary">
    <meta name="twitter:title" content="{page_title}" data-i18n-content="{title_key}">
    <meta name="twitter:description" content="{escaped_description}" data-i18n-content="{description_key}">
{FAVICON_LINKS}
    <link rel="stylesheet" href="/static/styles.css">
    <script type="application/ld+json">{structured_data}</script>
</head>
<body class="legal-body">
    <header class="landing-nav">
        <a class="landing-brand" href="/" aria-label="{business_name}">
            {BRAND_MARKUP}
        </a>
        <nav class="landing-nav-actions" aria-label="Navigation principale">
            <a href="/marches" data-i18n="nav_markets">Marchés</a>
            <a href="/market-pulse" data-i18n="nav_pulse">Market Pulse</a>
            <a href="/guides" data-i18n="nav_guides">Guides</a>
            <a href="/#pricing" data-i18n="nav_pricing">Formules</a>
            <a href="/support" data-i18n="nav_support">Support</a>
            <a href="/terminal" data-i18n="nav_terminal">Ouvrir le terminal</a>
            <button type="button" class="landing-lang" data-lang-toggle>EN</button>
        </nav>
    </header>
    <main class="legal-page">
        <div class="landing-kicker" data-i18n="{kicker_key}">{meta["kicker"]}</div>
        <h1 data-i18n="{title_key}">{meta["title"]}</h1>
        <section>
            <h2 data-i18n="legal_general">Informations générales</h2>
            <p>
                <span data-i18n="legal_editor">Éditeur</span> : {LEGAL_PUBLISHER_NAME}<br>
                <span data-i18n="legal_business">Entreprise</span> : {business_name}<br>
                <span data-i18n="legal_status">Statut</span> : {LEGAL_BUSINESS_STATUS}<br>
                <span data-i18n="legal_id">Identifiant</span> : {LEGAL_BUSINESS_ID}<br>
                <span data-i18n="legal_contact">Contact</span> : <a href="mailto:{email}">{email}</a><br>
                <span data-i18n="legal_address">Adresse</span> : {LEGAL_BUSINESS_ADDRESS}<br>
                <span data-i18n="legal_hosting">Hébergement</span> : {LEGAL_HOSTING_PROVIDER}{vat_line}
            </p>
        </section>
        {section_html}
        {terms_extra}
        <section class="legal-contact">
            <h2 data-i18n="legal_contact_title">Contact</h2>
            <p><span data-i18n="legal_contact_copy">Pour toute question relative aux conditions d'utilisation, à la confidentialité ou aux risques liés au trading, vous pouvez nous contacter à</span> <a href="mailto:{email}">{email}</a>.</p>
        </section>
    </main>
{PUBLIC_FOOTER}
    <script src="/static/landing.js"></script>
</body>
</html>"""


@router.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(localized_landing("fr"))


@router.head("/")
async def index_head():
    return FastAPIResponse(status_code=200)


@router.get("/terminal", response_class=HTMLResponse)
async def terminal():
    return FileResponse("templates/index.html", headers={"X-Robots-Tag": "noindex, follow"})


@router.head("/terminal")
async def terminal_head():
    return FastAPIResponse(status_code=200, headers={"X-Robots-Tag": "noindex, follow"})


@router.get("/account", response_class=HTMLResponse)
async def account_page():
    return FileResponse("templates/account.html", headers={"X-Robots-Tag": "noindex, nofollow"})


@router.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page():
    return FileResponse("templates/reset_password.html", headers={"X-Robots-Tag": "noindex, nofollow"})


@router.get("/ressources", response_class=HTMLResponse)
async def resources_index_page():
    return HTMLResponse(localize_html(resources_page(), "fr", "/ressources"))


@router.get("/guides", response_class=HTMLResponse)
async def guides_index_page():
    return HTMLResponse(localize_html(guides_page(), "fr", "/guides"))


@router.get("/market-pulse", response_class=HTMLResponse)
async def market_pulse_index_page():
    pulse = await build_public_market_pulse()
    return HTMLResponse(localize_html(market_pulse_page(pulse), "fr", "/market-pulse"))


@router.get("/marches", response_class=HTMLResponse)
async def markets_index_page_route():
    return HTMLResponse(localize_html(markets_index_page(), "fr", "/marches"))


@router.get("/marches/{slug}", response_class=HTMLResponse)
async def market_pair_page_route(slug: str):
    if slug not in FX_MARKET_BY_SLUG:
        return FastAPIResponse(status_code=404, content="Market not found")
    return HTMLResponse(localize_html(market_pair_page(slug), "fr", f"/marches/{slug}"))


@router.get("/support", response_class=HTMLResponse)
async def support_index_page():
    return HTMLResponse(localize_html(support_page(), "fr", "/support"))


@router.get("/terminal-xauusd", response_class=HTMLResponse)
async def terminal_xauusd_page():
    return HTMLResponse(localize_html(content_page("terminal_xauusd"), "fr", "/terminal-xauusd"))


@router.get("/calendrier-economique-or", response_class=HTMLResponse)
async def calendrier_economique_or_page():
    return HTMLResponse(localize_html(content_page("calendrier_or"), "fr", "/calendrier-economique-or"))


@router.get("/news-forex-or", response_class=HTMLResponse)
async def news_forex_or_page():
    return HTMLResponse(localize_html(content_page("news_forex_or"), "fr", "/news-forex-or"))


@router.get("/guide/trading-or-macro", response_class=HTMLResponse)
async def guide_trading_or_macro_page():
    return HTMLResponse(localize_html(content_page("guide_trading_or_macro"), "fr", "/guide/trading-or-macro"))


@router.get("/guides/routine-trading-xauusd", response_class=HTMLResponse)
async def routine_trading_xauusd_page():
    return HTMLResponse(localize_html(content_page("routine_trading_xauusd"), "fr", "/guides/routine-trading-xauusd"))


@router.get("/guides/dxy-taux-us-or", response_class=HTMLResponse)
async def dxy_taux_us_or_page():
    return HTMLResponse(localize_html(content_page("dxy_taux_or"), "fr", "/guides/dxy-taux-us-or"))


@router.get("/guides/bias-desk-trading", response_class=HTMLResponse)
async def bias_desk_trading_page():
    return HTMLResponse(localize_html(content_page("bias_desk"), "fr", "/guides/bias-desk-trading"))


@router.get("/terms", response_class=HTMLResponse)
async def terms_page():
    return HTMLResponse(localize_html(legal_page("terms_title", "terms_kicker", [
        ("terms_section1_title", "terms_section1"),
        ("terms_section2_title", "terms_section2"),
        ("terms_section3_title", "terms_section3"),
        ("terms_section4_title", "terms_section4"),
        ("terms_section5_title", "terms_section5"),
        ("terms_section6_title", "terms_section6"),
        ("terms_section7_title", "terms_section7"),
        ("terms_section8_title", "terms_section8"),
        ("terms_section9_title", "terms_section9"),
        ("terms_section10_title", "terms_section10"),
        ("terms_section11_title", "terms_section11"),
        ("terms_section12_title", "terms_section12"),
    ]), "fr", "/terms"))


@router.get("/privacy", response_class=HTMLResponse)
async def privacy_page():
    return HTMLResponse(localize_html(legal_page("privacy_title", "privacy_kicker", [
        ("privacy_section1_title", "privacy_section1"),
        ("privacy_section2_title", "privacy_section2"),
        ("privacy_section3_title", "privacy_section3"),
        ("privacy_section4_title", "privacy_section4"),
        ("privacy_section5_title", "privacy_section5"),
        ("privacy_section6_title", "privacy_section6"),
        ("privacy_section7_title", "privacy_section7"),
        ("privacy_section8_title", "privacy_section8"),
        ("privacy_section9_title", "privacy_section9"),
        ("privacy_section10_title", "privacy_section10"),
        ("privacy_section11_title", "privacy_section11"),
        ("privacy_section12_title", "privacy_section12"),
    ]), "fr", "/privacy"))


@router.get("/risk-disclaimer", response_class=HTMLResponse)
async def risk_disclaimer_page():
    return HTMLResponse(localize_html(legal_page("risk_title", "risk_kicker", [
        ("risk_section1_title", "risk_section1"),
        ("risk_section2_title", "risk_section2"),
        ("risk_section3_title", "risk_section3"),
        ("risk_section4_title", "risk_section4"),
        ("risk_section5_title", "risk_section5"),
        ("risk_section6_title", "risk_section6"),
    ]), "fr", "/risk-disclaimer"))


async def localized_public_page(locale: str, path: str = "/"):
    clean_path = path if path.startswith("/") else f"/{path}"
    if clean_path != "/" and clean_path.endswith("/"):
        clean_path = clean_path.rstrip("/")

    if locale == "fr":
        target = clean_path if clean_path != "/" else "/"
        return FastAPIResponse(status_code=308, headers={"Location": target})
    if locale not in SUPPORTED_LOCALES:
        return FastAPIResponse(status_code=404, content="Page not found")

    if clean_path == "/":
        return HTMLResponse(localized_landing(locale))
    if clean_path == "/ressources":
        return HTMLResponse(localize_html(resources_page(), locale, clean_path))
    if clean_path == "/guides":
        return HTMLResponse(localize_html(guides_page(), locale, clean_path))
    if clean_path == "/market-pulse":
        pulse = await build_public_market_pulse()
        return HTMLResponse(localize_html(market_pulse_page(pulse), locale, clean_path))
    if clean_path == "/marches":
        return HTMLResponse(localize_html(markets_index_page(), locale, clean_path))
    if clean_path.startswith("/marches/"):
        slug = clean_path.rsplit("/", 1)[-1]
        if slug not in FX_MARKET_BY_SLUG:
            return FastAPIResponse(status_code=404, content="Market not found")
        return HTMLResponse(localize_html(market_pair_page(slug), locale, clean_path))
    if clean_path == "/support":
        return HTMLResponse(localize_html(support_page(), locale, clean_path))

    content_routes = {
        "/terminal-xauusd": "terminal_xauusd",
        "/calendrier-economique-or": "calendrier_or",
        "/news-forex-or": "news_forex_or",
        "/guide/trading-or-macro": "guide_trading_or_macro",
        "/guides/routine-trading-xauusd": "routine_trading_xauusd",
        "/guides/dxy-taux-us-or": "dxy_taux_or",
        "/guides/bias-desk-trading": "bias_desk",
    }
    if clean_path in content_routes:
        return HTMLResponse(localize_html(content_page(content_routes[clean_path]), locale, clean_path))
    if clean_path == "/terms":
        return HTMLResponse(localize_html(legal_page("terms_title", "terms_kicker", [
            ("terms_section1_title", "terms_section1"),
            ("terms_section2_title", "terms_section2"),
            ("terms_section3_title", "terms_section3"),
            ("terms_section4_title", "terms_section4"),
            ("terms_section5_title", "terms_section5"),
            ("terms_section6_title", "terms_section6"),
            ("terms_section7_title", "terms_section7"),
            ("terms_section8_title", "terms_section8"),
            ("terms_section9_title", "terms_section9"),
            ("terms_section10_title", "terms_section10"),
            ("terms_section11_title", "terms_section11"),
            ("terms_section12_title", "terms_section12"),
        ]), locale, clean_path))
    if clean_path == "/privacy":
        return HTMLResponse(localize_html(legal_page("privacy_title", "privacy_kicker", [
            ("privacy_section1_title", "privacy_section1"),
            ("privacy_section2_title", "privacy_section2"),
            ("privacy_section3_title", "privacy_section3"),
            ("privacy_section4_title", "privacy_section4"),
            ("privacy_section5_title", "privacy_section5"),
            ("privacy_section6_title", "privacy_section6"),
            ("privacy_section7_title", "privacy_section7"),
            ("privacy_section8_title", "privacy_section8"),
            ("privacy_section9_title", "privacy_section9"),
            ("privacy_section10_title", "privacy_section10"),
            ("privacy_section11_title", "privacy_section11"),
            ("privacy_section12_title", "privacy_section12"),
        ]), locale, clean_path))
    if clean_path == "/risk-disclaimer":
        return HTMLResponse(localize_html(legal_page("risk_title", "risk_kicker", [
            ("risk_section1_title", "risk_section1"),
            ("risk_section2_title", "risk_section2"),
            ("risk_section3_title", "risk_section3"),
            ("risk_section4_title", "risk_section4"),
            ("risk_section5_title", "risk_section5"),
            ("risk_section6_title", "risk_section6"),
        ]), locale, clean_path))

    return FastAPIResponse(status_code=404, content="Page not found")


def robots_txt_content() -> str:
    return f"""User-agent: *
Allow: /
Disallow: /admin
Disallow: /db-test
Disallow: /api/
Disallow: /ws/

Sitemap: {absolute_url('/sitemap.xml')}
"""


@router.api_route("/robots.txt", methods=["GET", "HEAD"], response_class=PlainTextResponse)
async def robots_txt():
    return robots_txt_content()


@router.api_route("/favicon.ico", methods=["GET", "HEAD"], include_in_schema=False)
async def favicon():
    return FileResponse("static/favicon.ico", media_type="image/x-icon")


def sitemap_xml_content() -> str:
    urls = [
        ("/", "daily", "1.0"),
        ("/support", "weekly", "0.7"),
        ("/ressources", "weekly", "0.8"),
        ("/guides", "weekly", "0.8"),
        ("/market-pulse", "daily", "0.9"),
        ("/marches", "weekly", "0.9"),
        *[(f"/marches/{pair['slug']}", "weekly", "0.8") for pair in FX_MARKET_PAIRS],
        ("/terminal-xauusd", "weekly", "0.8"),
        ("/calendrier-economique-or", "weekly", "0.8"),
        ("/news-forex-or", "weekly", "0.8"),
        ("/guide/trading-or-macro", "weekly", "0.8"),
        ("/guides/routine-trading-xauusd", "weekly", "0.8"),
        ("/guides/dxy-taux-us-or", "weekly", "0.8"),
        ("/guides/bias-desk-trading", "weekly", "0.8"),
        ("/terms", "monthly", "0.5"),
        ("/privacy", "monthly", "0.5"),
        ("/risk-disclaimer", "monthly", "0.5"),
    ]
    localized_urls = [
        (locale_path(path, locale), changefreq, priority)
        for path, changefreq, priority in urls
        for locale in SUPPORTED_LOCALES
    ]
    items = "\n".join(
        f"""  <url>
    <loc>{absolute_url(localized_path)}</loc>
    <changefreq>{changefreq}</changefreq>
    <priority>{priority}</priority>
  </url>"""
        for localized_path, changefreq, priority in localized_urls
    )
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{items}
</urlset>
"""
    return xml


@router.api_route("/sitemap.xml", methods=["GET", "HEAD"])
async def sitemap_xml():
    return FastAPIResponse(content=sitemap_xml_content(), media_type="application/xml")


@router.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    require_owner(request)
    return FileResponse("templates/admin.html")


@router.get("/healthz")
async def healthz():
    return {"status": "ok"}


@router.head("/healthz")
async def healthz_head():
    return FastAPIResponse(status_code=200)


@router.get("/db-test")
def db_test(request: Request):
    require_owner(request)
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        result = cur.fetchone()
        cur.close()
        conn.close()

        return {"database": "ok", "result": result[0]}
    except Exception:
        return {"database": "error"}


@router.get("/{locale}", response_class=HTMLResponse)
async def localized_home(locale: str):
    return await localized_public_page(locale, "/")


@router.get("/{locale}/{path:path}", response_class=HTMLResponse)
async def localized_public_route(locale: str, path: str):
    return await localized_public_page(locale, f"/{path}")


PUBLIC_HEAD_PATHS = {
    "/",
    "/support",
    "/ressources",
    "/guides",
    "/market-pulse",
    "/marches",
    "/terminal-xauusd",
    "/calendrier-economique-or",
    "/news-forex-or",
    "/guide/trading-or-macro",
    "/guides/routine-trading-xauusd",
    "/guides/dxy-taux-us-or",
    "/guides/bias-desk-trading",
    "/terms",
    "/privacy",
    "/risk-disclaimer",
}


def public_head_response(path: str) -> FastAPIResponse:
    clean_path = f"/{path.strip('/')}" if path else "/"
    if clean_path != "/" and clean_path.endswith("/"):
        clean_path = clean_path.rstrip("/")

    if clean_path == "/terminal":
        return FastAPIResponse(status_code=200, headers={"X-Robots-Tag": "noindex, follow"})
    if clean_path in {"/account", "/reset-password"}:
        return FastAPIResponse(status_code=200, headers={"X-Robots-Tag": "noindex, nofollow"})

    segments = clean_path.strip("/").split("/", 1) if clean_path != "/" else []
    if segments and segments[0] in SUPPORTED_LOCALES:
        locale = segments[0]
        base_path = f"/{segments[1]}" if len(segments) > 1 else "/"
        if locale == "fr":
            return FastAPIResponse(status_code=308, headers={"Location": base_path})
    else:
        base_path = clean_path

    if base_path in PUBLIC_HEAD_PATHS:
        return FastAPIResponse(status_code=200)
    if base_path.startswith("/marches/"):
        slug = base_path.rsplit("/", 1)[-1]
        if slug in FX_MARKET_BY_SLUG:
            return FastAPIResponse(status_code=200)
    return FastAPIResponse(status_code=404)


@router.head("/{path:path}")
async def public_head_route(path: str):
    return public_head_response(path)
