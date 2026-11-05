package com.exemplo.vendaswhatsapp;

import android.animation.Animator;
import android.animation.AnimatorListenerAdapter;
import android.animation.ValueAnimator;
import android.app.Activity;
import android.app.AlarmManager;
import android.app.AlertDialog;
import android.app.DatePickerDialog;
import android.app.Dialog;
import android.Manifest;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.NotificationChannel;
import android.content.ActivityNotFoundException;
import android.content.ClipboardManager;
import android.content.Intent;
import android.content.Context;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.content.pm.PackageInstaller;
import android.net.Uri;
import android.content.ContentValues;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RectF;
import android.graphics.Rect;
import android.graphics.drawable.GradientDrawable;
import android.graphics.pdf.PdfDocument;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import android.provider.Settings;
import android.speech.RecognitionListener;
import android.speech.RecognizerIntent;
import android.speech.SpeechRecognizer;
import android.speech.tts.TextToSpeech;
import android.speech.tts.UtteranceProgressListener;
import android.text.Editable;
import android.text.InputType;
import android.text.TextWatcher;
import android.text.method.DigitsKeyListener;
import android.util.Base64;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewParent;
import android.widget.ArrayAdapter;
import android.widget.AdapterView;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.ScrollView;
import android.widget.Spinner;
import android.widget.Switch;
import android.widget.TextView;
import android.widget.Toast;
import android.view.inputmethod.InputMethodManager;

import java.text.NumberFormat;
import java.text.SimpleDateFormat;
import java.text.Collator;
import java.io.BufferedInputStream;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.Calendar;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.Collections;
import java.text.Normalizer;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.concurrent.Executor;
import org.json.JSONObject;
import org.json.JSONArray;

import androidx.biometric.BiometricManager;
import androidx.biometric.BiometricPrompt;
import androidx.core.content.ContextCompat;
import androidx.fragment.app.FragmentActivity;
import androidx.security.crypto.EncryptedSharedPreferences;
import androidx.security.crypto.MasterKey;

import com.github.mikephil.charting.charts.BarChart;
import com.github.mikephil.charting.charts.LineChart;
import com.github.mikephil.charting.components.AxisBase;
import com.github.mikephil.charting.components.Legend;
import com.github.mikephil.charting.components.LimitLine;
import com.github.mikephil.charting.components.XAxis;
import com.github.mikephil.charting.components.YAxis;
import com.github.mikephil.charting.data.BarData;
import com.github.mikephil.charting.data.BarDataSet;
import com.github.mikephil.charting.data.BarEntry;
import com.github.mikephil.charting.data.Entry;
import com.github.mikephil.charting.data.LineData;
import com.github.mikephil.charting.data.LineDataSet;
import com.github.mikephil.charting.formatter.ValueFormatter;

public class MainActivity extends FragmentActivity {
    private static final class ModuloHome {
        final String titulo;
        final String descricao;
        final String categoria;
        final String sigla;
        final int cor;
        final Runnable acao;

        ModuloHome(String titulo, String descricao, String categoria, String sigla, int cor, Runnable acao) {
            this.titulo = titulo;
            this.descricao = descricao;
            this.categoria = categoria;
            this.sigla = sigla;
            this.cor = cor;
            this.acao = acao;
        }
    }

    private static final class SessaoExpiradaException extends Exception {
        SessaoExpiradaException(String message) { super(message); }
    }
    private static final int COR_FUNDO_ESCURO = Color.rgb(244, 247, 244);
    private static final int COR_CARD_ESCURO = Color.WHITE;
    private static final int COR_CARD_ESCURO_2 = Color.rgb(247, 250, 247);
    private static final int COR_TEXTO_CLARO = Color.rgb(23, 33, 43);
    private static final int COR_TEXTO_SUAVE = Color.rgb(102, 116, 135);
    private static final String SERVER_BASE_URL = BuildConfig.SERVER_BASE_URL;
    private static final String UPDATE_URL = SERVER_BASE_URL + "/app-updates/latest.json";
    private static final String AUTH_LOGIN_URL = SERVER_BASE_URL + "/api/auth/login";
    private static final String AUTH_ME_URL = SERVER_BASE_URL + "/api/auth/me";
    private static final String AUTH_LOGOUT_URL = SERVER_BASE_URL + "/api/auth/logout";
    private static final String SALES_URL = SERVER_BASE_URL + "/api/sales";
    private static final String SALES_BULK_DELIVERED_URL = SERVER_BASE_URL + "/api/sales/bulk-delivered";
    private static final String APP_NOTES_URL = SERVER_BASE_URL + "/api/app-notes/mobile";
    private static final String APP_NOTES_MATCHES_URL = SERVER_BASE_URL + "/api/app-notes/mobile/matches";
    private static final String MONTEIRO_PRODUCTS_URL = SERVER_BASE_URL + "/api/monteiro/products";
    private static final String VALES_URL = SERVER_BASE_URL + "/api/mobile/vales";
    private static final String MOBILE_BOLETOS_CONFIG_URL = "/api/mobile/boletos/config";
    private static final String MOBILE_BOLETOS_OVERDUE_URL = "/api/mobile/boletos/overdue";
    static final String APP_CALENDAR_URL = SERVER_BASE_URL + "/api/app-calendar/mobile";
    private static final String APP_NOTES_TOKEN = BuildConfig.APP_NOTES_TOKEN;
    static final String APP_CALENDAR_TOKEN = APP_NOTES_TOKEN;
    static final String EXTRA_OPEN_CALENDAR_NOTIFICATIONS = "open_calendar_notifications";
    private static final long PIN_TEMPO_CONFIAVEL_MS = 15L * 60L * 1000L;
    private static final String[] CLIENTES_PADRAO = {"PALADAR DISTRITO", "PALADAR BASE", "SESAU", "MATERNIDADE", "HGR", "OUTRO"};
    private final List<ItemPedido> itens = new ArrayList<>();
    private final NumberFormat moeda = NumberFormat.getCurrencyInstance(new Locale("pt", "BR"));
    private EditText clienteOutro, data, peso, valor;
    private Spinner cliente, produto, unidade;
    private ArrayAdapter<String> produtosAdapter;
    private final List<String> produtos = new ArrayList<>();
    private LinearLayout listaItens;
    private TextView totalText;
    private Button enviarSistemaButton, pendentesButton;
    private EditText valeSolicitante, valeValor, valeData;
    private SignatureView valeAssinatura;
    private ValesDatabase valesDatabase;
    private String pedidoId = UUID.randomUUID().toString();
    private boolean produtoInicializado = false;
    private boolean servicosPosLoginIniciados = false;
    private String telaAtual = "auth";
    private boolean temaEscuroAtivo = false;
    private static final int PEDIDO_AUDIO_VOZ = 7104;
    private SpeechRecognizer reconhecedorVoz;
    private TextToSpeech falaVoz;
    private LinearLayout vozRaiz, vozLista;
    private TextView vozPergunta, vozEstado, vozClienteData, vozSecaoProdutos;
    private Button vozMicrofone;
    private Button vozSim, vozNao;
    private final List<ItemInterpretado> itensVoz = new ArrayList<>();
    private String clienteVoz = "";
    private String dataVoz = "";
    private String etapaVoz = "";
    private boolean falaPronta = false;
    private boolean escutaVozAtiva = false;
    private boolean envioOrigemVoz = false;
    private ItemInterpretado itemNovoPendente;
    private boolean rascunhoPronto = false;
    private boolean suspenderRascunho = false;
    private boolean listenersRascunhoAtivos = false;
    private TextView statusEnvioView;
    private final Handler rascunhoHandler = new Handler(Looper.getMainLooper());
    private Runnable salvarRascunhoAgendado;
    private long tentativaEscutaVoz = 0;

    private interface CatalogoSyncCallback {
        void concluir(boolean disponivel, boolean atualizado);
    }

    private interface DestinoUnificacaoCallback {
        void continuar(String noteId);
    }

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        mostrarAberturaAnimada(this::abrirFluxoInicial);
    }

    private void mostrarAberturaAnimada(Runnable aoConcluir) {
        int variacao = new java.util.Random().nextInt(3);
        FrameLayout tela = new FrameLayout(this);
        AberturaAnimadaView animacao = new AberturaAnimadaView(variacao);
        tela.addView(animacao, new FrameLayout.LayoutParams(-1, -1));
        getWindow().setStatusBarColor(Color.rgb(4, 34, 25));
        getWindow().setNavigationBarColor(Color.rgb(4, 34, 25));
        setContentView(tela);

        ValueAnimator andamento = ValueAnimator.ofFloat(0f, 1f);
        andamento.setDuration(3600);
        andamento.addUpdateListener(a -> animacao.setAndamento((Float) a.getAnimatedValue()));
        andamento.addListener(new AnimatorListenerAdapter() {
            private boolean concluido;
            private void seguir() {
                if (concluido || isFinishing() || isDestroyed()) return;
                concluido = true;
                aoConcluir.run();
            }
            @Override public void onAnimationEnd(Animator animation) { seguir(); }
            @Override public void onAnimationCancel(Animator animation) { seguir(); }
        });
        andamento.start();
    }

    private final class AberturaAnimadaView extends View {
        private final int variacao;
        private final Bitmap quadros;
        private final Paint arte = new Paint(Paint.ANTI_ALIAS_FLAG | Paint.FILTER_BITMAP_FLAG);
        private final Paint nomeContorno = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Paint nomeTexto = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Paint riscoLuz = new Paint(Paint.ANTI_ALIAS_FLAG);
        private float andamento;

        AberturaAnimadaView(int variacao) {
            super(MainActivity.this);
            this.variacao = variacao;
            this.quadros = BitmapFactory.decodeResource(getResources(), R.drawable.intro_frames);
            arte.setFilterBitmap(true);
            nomeContorno.setColor(Color.rgb(4, 40, 29));
            nomeContorno.setStyle(Paint.Style.STROKE);
            nomeContorno.setStrokeJoin(Paint.Join.ROUND);
            nomeContorno.setStrokeWidth(dp(5));
            nomeContorno.setTypeface(android.graphics.Typeface.create("sans-serif-black", android.graphics.Typeface.BOLD));
            nomeTexto.setColor(Color.rgb(204, 28, 38));
            nomeTexto.setTextAlign(Paint.Align.CENTER);
            nomeTexto.setTypeface(android.graphics.Typeface.create("sans-serif-black", android.graphics.Typeface.BOLD));
            nomeTexto.setShadowLayer(dp(5), 0, dp(2), Color.WHITE);
            riscoLuz.setColor(Color.rgb(65, 211, 255));
            riscoLuz.setStyle(Paint.Style.STROKE);
            riscoLuz.setStrokeCap(Paint.Cap.ROUND);
            riscoLuz.setStrokeWidth(dp(3));
            riscoLuz.setShadowLayer(dp(10), 0, 0, Color.rgb(0, 191, 255));
        }

        void setAndamento(float valor) {
            andamento = valor;
            invalidate();
        }

        @Override protected void onDraw(Canvas canvas) {
            super.onDraw(canvas);
            float w = getWidth(), h = getHeight();
            float progresso = Math.max(0f, Math.min(1f, andamento));
            if (quadros == null || w <= 0 || h <= 0) return;

            final int colunas = 4, linhas = 3;
            int larguraQuadro = quadros.getWidth() / colunas;
            int alturaQuadro = quadros.getHeight() / linhas;
            float posicaoQuadro = progresso * (colunas - 1);
            int quadroAtual = Math.min(colunas - 1, (int) posicaoQuadro);
            int proximoQuadro = Math.min(colunas - 1, quadroAtual + 1);
            float mistura = quadroAtual == proximoQuadro ? 0f : posicaoQuadro - quadroAtual;

            float escala = Math.max(w / larguraQuadro, h / alturaQuadro) * (1.02f + .025f * progresso);
            float largura = larguraQuadro * escala;
            float altura = alturaQuadro * escala;
            float deslocamentoX = (float) Math.sin(progresso * Math.PI) * w * .018f;
            RectF destino = new RectF((w - largura) * .5f + deslocamentoX,
                (h - altura) * .5f, (w + largura) * .5f + deslocamentoX, (h + altura) * .5f);
            canvas.save();
            canvas.clipRect(0, 0, w, h);
            desenharQuadro(canvas, quadroAtual, larguraQuadro, alturaQuadro, destino, 255);
            if (proximoQuadro != quadroAtual && mistura > 0f) {
                desenharQuadro(canvas, proximoQuadro, larguraQuadro, alturaQuadro, destino,
                    Math.round(255 * mistura));
            }
            desenharNomeAnimado(canvas, w, h, progresso);
            canvas.restore();
        }

        private void desenharNomeAnimado(Canvas canvas, float largura, float altura, float progresso) {
            if (progresso <= .55f) return;
            float entrada = Math.min(1f, (progresso - .55f) / .25f);
            float suavizado = entrada * entrada * (3f - 2f * entrada);
            int alpha = Math.round(255 * suavizado);
            float centroX = largura * .5f;
            float escala = .88f + .12f * suavizado;
            canvas.save();
            canvas.translate(centroX, altura * .84f + (1f - suavizado) * dp(20));
            canvas.scale(escala, escala);

            nomeContorno.setTextSize(dp(18));
            nomeContorno.setAlpha(alpha);
            nomeTexto.setTextSize(dp(18));
            nomeTexto.setAlpha(alpha);
            canvas.drawText("MENINA DOS", 0, 0, nomeContorno);
            canvas.drawText("MENINA DOS", 0, 0, nomeTexto);

            nomeContorno.setTextSize(dp(30));
            nomeTexto.setTextSize(dp(30));
            canvas.drawText("RAIOS", 0, dp(34), nomeContorno);
            canvas.drawText("RAIOS", 0, dp(34), nomeTexto);

            riscoLuz.setAlpha(alpha);
            float meiaLinha = Math.min(largura * .23f, dp(82)) * suavizado;
            canvas.drawLine(-meiaLinha, dp(42), meiaLinha, dp(42), riscoLuz);
            canvas.restore();
        }

        private void desenharQuadro(Canvas canvas, int coluna, int largura, int altura,
                                     RectF destino, int alpha) {
            Rect origem = new Rect(coluna * largura, variacao * altura,
                (coluna + 1) * largura, (variacao + 1) * altura);
            arte.setAlpha(alpha);
            canvas.drawBitmap(quadros, origem, destino, arte);
        }
    }

    @Override protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        if (servicosPosLoginIniciados && adminNotificacoes()) abrirCalendarioSeSolicitado();
    }

    @Override protected void onDestroy() {
        liberarReconhecedorVoz();
        if (falaVoz != null) { falaVoz.stop(); falaVoz.shutdown(); falaVoz = null; }
        super.onDestroy();
    }

    @Override protected void onResume() {
        super.onResume();
        // Recria os alarmes quando o admin volta das configurações do Android
        // ou reabre o APK após o sistema ter encerrado o processo em segundo plano.
        if (servicosPosLoginIniciados && adminNotificacoes()) {
            CalendarNotificationReceiver.agendar(this);
            NewTempoCollectionReceiver.agendar(this);
        }
    }

    @Override protected void onPause() {
        if ("pedido".equals(telaAtual) && rascunhoPronto) salvarRascunhoNota();
        if ("entrega_voz".equals(telaAtual)) guardarRascunhoVoz();
        super.onPause();
    }

    private void abrirFluxoInicial() {
        limparDadosPinAntigos();
        if (!adminNotificacoes()) {
            CalendarNotificationReceiver.cancelar(this);
            NewTempoCollectionReceiver.cancelar(this);
        }
        if (tokenSistema().isEmpty()) {
            mostrarLoginSistema();
        } else {
            validarSessaoSalvaAoAbrir();
        }
    }

    private void validarSessaoSalvaAoAbrir() {
        telaAtual = "auth";
        ScrollView scroll = new ScrollView(this);
        scroll.setBackgroundColor(COR_FUNDO_ESCURO);
        LinearLayout raiz = coluna();
        raiz.setBackgroundColor(COR_FUNDO_ESCURO);
        raiz.setPadding(dp(24), dp(42), dp(24), dp(32));
        scroll.addView(raiz);
        TextView titulo = texto("Validando sessao", 24, true);
        titulo.setGravity(Gravity.CENTER_HORIZONTAL);
        raiz.addView(titulo);
        TextView sub = texto("Aguarde enquanto verificamos seu acesso.", 15, false);
        sub.setGravity(Gravity.CENTER_HORIZONTAL);
        raiz.addView(sub);
        setContentView(scroll);
        new Thread(() -> {
            try {
                JSONObject me = buscarAuthMe();
                atualizarUsuarioSessao(me);
                runOnUiThread(() -> {
                    if (biometriaAtiva()) mostrarTelaBiometria();
                    else iniciarAppLogado();
                });
            } catch (Exception e) {
                if (e instanceof SessaoExpiradaException) {
                    limparCredenciaisSessaoExpirada();
                    runOnUiThread(() -> mostrarLoginSistema());
                } else {
                    runOnUiThread(() -> mostrarFalhaDeConexao(this::validarSessaoSalvaAoAbrir));
                }
            }
        }).start();
    }

    private void iniciarAppLogado() {
        if (!adminNotificacoes()) {
            CalendarNotificationReceiver.cancelar(this);
            NewTempoCollectionReceiver.cancelar(this);
        }
        if (!servicosPosLoginIniciados) {
            solicitarPermissaoNotificacoes();
            android.content.SharedPreferences motivacao = getSharedPreferences("daily_motivation", MODE_PRIVATE);
            if (adminNotificacoes() && motivacao.getBoolean("enabled", false)) DailyMotivationReceiver.agendar(this, motivacao.getString("time", "07:00"));
            if (adminNotificacoes()) {
                CalendarNotificationReceiver.agendar(this);
                NewTempoCollectionReceiver.agendar(this);
            }
            if (atualizacaoPropriaAtiva()) verificarAtualizacao(false);
            servicosPosLoginIniciados = true;
        }
        sincronizarValesPendentesSilencioso();
        mostrarHomeModulos();
        abrirCalendarioSeSolicitado();
    }

    private void abrirCalendarioSeSolicitado() {
        Intent intent = getIntent();
        if (intent == null || !intent.getBooleanExtra(EXTRA_OPEN_CALENDAR_NOTIFICATIONS, false)) return;
        intent.removeExtra(EXTRA_OPEN_CALENDAR_NOTIFICATIONS);
        if (adminNotificacoes()) abrirCalendarioNotificacoes();
    }

    private void mostrarHomeModulos() {
        temaEscuroAtivo = true;
        telaAtual = "home";
        esconderTeclado();
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(COR_FUNDO_ESCURO);
        LinearLayout raiz = coluna();
        raiz.setBackgroundColor(COR_FUNDO_ESCURO);
        raiz.setPadding(dp(16), dp(16), dp(16), dp(26));
        scroll.addView(raiz);

        LinearLayout cabecalho = new LinearLayout(this);
        cabecalho.setOrientation(LinearLayout.HORIZONTAL);
        cabecalho.setGravity(Gravity.CENTER_VERTICAL);
        ImageView logo = new ImageView(this);
        logo.setImageResource(com.exemplo.vendaswhatsapp.R.drawable.logo);
        logo.setScaleType(ImageView.ScaleType.CENTER_INSIDE);
        LinearLayout.LayoutParams logoParams = new LinearLayout.LayoutParams(dp(54), dp(54));
        logoParams.setMargins(0, 0, dp(12), 0);
        cabecalho.addView(logo, logoParams);
        LinearLayout identificacao = coluna();
        String nome = authPrefs().getString("full_name", "").trim();
        if (nome.isEmpty()) nome = authPrefs().getString("username", "").trim();
        if (nome.contains(" ")) nome = nome.substring(0, nome.indexOf(' '));
        identificacao.addView(texto(nome.isEmpty() ? "Olá" : "Olá, " + nome, 21, true));
        identificacao.addView(texto("Menina dos Raios · Vendas", 12, false));
        cabecalho.addView(identificacao, new LinearLayout.LayoutParams(0, -2, 1));
        if (adminNotificacoes()) {
            TextView sino = texto("🔔", 22, true);
            sino.setGravity(Gravity.CENTER);
            sino.setBackground(fundoComBorda(Color.WHITE, Color.rgb(216, 227, 220), 12));
            sino.setContentDescription("Abrir central de notificações");
            cabecalho.addView(sino, new LinearLayout.LayoutParams(dp(48), dp(48)));
            sino.setOnClickListener(v -> abrirCentralNotificacoes("calendario"));
        }
        raiz.addView(cabecalho);

        TextView chamada = texto("Seu dia, em um só lugar", 23, true);
        chamada.setTextColor(Color.rgb(20, 83, 45));
        chamada.setPadding(0, dp(20), 0, dp(3));
        raiz.addView(chamada);
        TextView apoio = texto("Acesse uma operação ou acompanhe os resultados.", 13, false);
        apoio.setPadding(0, 0, 0, dp(10));
        raiz.addView(apoio);
        LinearLayout resumoDia = new LinearLayout(this);
        resumoDia.setOrientation(LinearLayout.VERTICAL);
        resumoDia.setVisibility(View.GONE);
        LinearLayout.LayoutParams resumoDiaParams = new LinearLayout.LayoutParams(-1, -2);
        resumoDiaParams.setMargins(0, 0, 0, dp(12));
        raiz.addView(resumoDia, resumoDiaParams);
        carregarResumoHome(resumoDia);

        LinearLayout destaqueDia = new LinearLayout(this);
        destaqueDia.setOrientation(LinearLayout.VERTICAL);
        destaqueDia.setPadding(dp(16), dp(14), dp(16), dp(14));
        destaqueDia.setBackground(fundoComBorda(Color.rgb(21, 101, 52), Color.rgb(21, 101, 52), 14));
        TextView destaqueTitulo = texto("OPERAÇÃO DO DIA", 11, true);
        destaqueTitulo.setTextColor(Color.rgb(207, 245, 218));
        destaqueDia.addView(destaqueTitulo);
        TextView destaqueTexto = texto("Registre uma entrega e acompanhe as notas em um só lugar.", 15, true);
        destaqueTexto.setTextColor(Color.WHITE);
        destaqueTexto.setPadding(0, dp(4), 0, dp(10));
        destaqueDia.addView(destaqueTexto);
        Button iniciarEntrega = botao("🚚    Nova entrega    →", Color.WHITE);
        iniciarEntrega.setTextColor(Color.rgb(20, 83, 45));
        iniciarEntrega.setBackground(fundoComBorda(Color.WHITE, Color.WHITE, 10));
        iniciarEntrega.setTextSize(17);
        iniciarEntrega.setContentDescription("Lançar nova entrega por voz");
        iniciarEntrega.setOnClickListener(v -> iniciarEntregaPorVoz());
        destaqueDia.addView(iniciarEntrega, new LinearLayout.LayoutParams(-1, dp(44)));
        LinearLayout.LayoutParams destaqueParams = new LinearLayout.LayoutParams(-1, -2);
        destaqueParams.setMargins(0, 0, 0, dp(12));
        raiz.addView(destaqueDia, destaqueParams);
        TextView mensagemDoDia = texto("Carregando mensagem do dia...", 14, true);
        mensagemDoDia.setPadding(dp(14), dp(12), dp(14), dp(12));
        mensagemDoDia.setBackground(fundoComBorda(Color.rgb(240, 248, 242), Color.rgb(205, 225, 209), 12));
        LinearLayout.LayoutParams mensagemParams = new LinearLayout.LayoutParams(-1, -2);
        mensagemParams.setMargins(0, 0, 0, dp(12));
        carregarMensagemMotivacional(mensagem -> {
            if (!"home".equals(telaAtual)) return;
            mensagemDoDia.setText(mensagem.isEmpty() ? "Mensagem motivacional indisponível no ERP hoje." : "Mensagem do dia\n" + mensagem);
        });
        List<ModuloHome> modulos = new ArrayList<>();
        modulos.add(new ModuloHome("Entregas", "Novo pedido por voz e acompanhamento das notas", "Operação", "EN", Color.rgb(245, 124, 0), () -> mostrarMenuEntregas()));
        modulos.add(new ModuloHome("Vale", "Solicitação com assinatura", "Operação", "VA", Color.rgb(202, 138, 4), () -> abrirModuloVale()));
        modulos.add(new ModuloHome("Dados dos vales", "Consultar solicitações", "Operação", "DV", Color.rgb(14, 165, 233), () -> abrirModuloDadosVales("")));
        modulos.add(new ModuloHome("Estoque", "Consultar saldos e registrar entradas", "Operação", "ES", Color.rgb(21, 128, 61), () -> abrirModuloEstoque("raios")));
        if ("admin".equalsIgnoreCase(authPrefs().getString("role", "").trim())) {
            modulos.add(new ModuloHome("Boletos", "Atrasos e clientes acompanhados", "Operação", "BO", Color.rgb(22, 101, 58), () -> abrirModuloBoletos()));
        }
        modulos.add(new ModuloHome("Projeção", "Estimativa de saída", "Análises", "PR", Color.rgb(59, 130, 246), () -> abrirModuloProjecao("30", "", "", "consolidada")));
        modulos.add(new ModuloHome("Avarias", "Ocorrências por período", "Análises", "AV", Color.rgb(220, 38, 38), () -> abrirModuloAvarias("mes")));
        modulos.add(new ModuloHome("Produtividade", "Resumo da equipe", "Análises", "PD", Color.rgb(22, 163, 74), () -> abrirModuloProdutividade("mes")));
        modulos.add(new ModuloHome("Clientes", "Busca e detalhes", "Análises", "CL", Color.rgb(59, 130, 246), () -> abrirModuloClientes("")));
        modulos.add(new ModuloHome("Consolidado", "Totais do período", "Análises", "CO", Color.rgb(168, 85, 247), () -> abrirModuloConsolidado("mes")));
        modulos.add(new ModuloHome("Análises", "Vendas, perdas e desempenho", "Análises", "AN", Color.rgb(22, 101, 58), () -> abrirPainelAnalises("mes")));
        modulos.add(new ModuloHome("Produtos", "Consultar preços de venda", "Análises", "PR", Color.rgb(13, 148, 136), () -> abrirModuloProdutos()));
        if (adminNotificacoes()) modulos.add(new ModuloHome("Notificações", "Calendário e alertas", "Mais", "NO", Color.rgb(99, 102, 241), () -> abrirCentralNotificacoes("calendario")));
        modulos.add(new ModuloHome("Sincronização ERP", "Atualizar dados do sistema", "Mais", "SI", Color.rgb(13, 148, 136), () -> abrirSincronizacaoERP()));
        modulos.add(new ModuloHome("Atualizações", "Verificar nova versão", "Mais", "AT", Color.rgb(148, 163, 184), () -> verificarAtualizacao(true)));

        String[] titulosAtalhos = {"Entregas", "Estoque", "Vale", "Boletos", "Análises", "Projeção", "Avarias", "Produtividade"};
        List<ModuloHome> modulosComplementares = new ArrayList<>();
        for (ModuloHome modulo : modulos) if (!Arrays.asList(titulosAtalhos).contains(modulo.titulo)) modulosComplementares.add(modulo);
        LinearLayout atalhosRapidos = coluna();
        raiz.addView(atalhosRapidos);
        adicionarGradeAtalhosHome(atalhosRapidos, "Operação", filtrarModulos(modulos, new String[]{"Entregas", "Estoque", "Vale", "Boletos"}));
        adicionarGradeAtalhosHome(atalhosRapidos, "Análises", filtrarModulos(modulos, new String[]{"Análises", "Projeção", "Avarias", "Produtividade"}));
        raiz.addView(mensagemDoDia, mensagemParams);

        EditText busca = campo("Buscar módulo", InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS);
        LinearLayout.LayoutParams buscaParams = new LinearLayout.LayoutParams(-1, dp(48));
        buscaParams.setMargins(0, 0, 0, dp(10));
        raiz.addView(busca, buscaParams);

        LinearLayout listaModulos = coluna();
        raiz.addView(listaModulos);
        carregarProdutos();
        LinearLayout atalhosCatalogo = new LinearLayout(this);
        atalhosCatalogo.setOrientation(LinearLayout.HORIZONTAL);
        Button novoProdutoHome = botao("＋ Novo produto", Color.rgb(21, 101, 52));
        novoProdutoHome.setTextSize(12);
        novoProdutoHome.setOnClickListener(v -> cadastrarNovoProduto());
        LinearLayout.LayoutParams novoProdutoHomeParams = new LinearLayout.LayoutParams(0, dp(48), 1);
        novoProdutoHomeParams.setMargins(0, dp(10), dp(5), 0);
        atalhosCatalogo.addView(novoProdutoHome, novoProdutoHomeParams);
        Button gerenciarCatalogoHome = botao("▤ Gerenciar catálogo", Color.rgb(20, 83, 45));
        gerenciarCatalogoHome.setTextSize(12);
        gerenciarCatalogoHome.setOnClickListener(v -> gerenciarProdutos());
        LinearLayout.LayoutParams gerenciarHomeParams = new LinearLayout.LayoutParams(0, dp(48), 1);
        gerenciarHomeParams.setMargins(dp(5), dp(10), 0, 0);
        atalhosCatalogo.addView(gerenciarCatalogoHome, gerenciarHomeParams);
        raiz.addView(atalhosCatalogo);
        renderizarModulosHome(listaModulos, modulosComplementares, "");
        busca.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            @Override public void onTextChanged(CharSequence s, int start, int before, int count) {
                String consulta = s == null ? "" : s.toString();
                boolean buscando = !consulta.trim().isEmpty();
                atalhosRapidos.setVisibility(buscando ? View.GONE : View.VISIBLE);
                renderizarModulosHome(listaModulos, buscando ? modulos : modulosComplementares, consulta);
            }
            @Override public void afterTextChanged(Editable s) {}
        });

        Button sairConta = botao("Sair da conta", Color.rgb(107, 114, 128));
        LinearLayout.LayoutParams sairParams = new LinearLayout.LayoutParams(-1, dp(44));
        sairParams.setMargins(0, dp(18), 0, 0);
        raiz.addView(sairConta, sairParams);
        sairConta.setOnClickListener(v -> sairDaConta(true));

        setContentView(scroll);
    }

    private List<ModuloHome> filtrarModulos(List<ModuloHome> modulos, String[] titulos) {
        List<ModuloHome> resultado = new ArrayList<>();
        for (String titulo : titulos) for (ModuloHome modulo : modulos) if (titulo.equals(modulo.titulo)) resultado.add(modulo);
        return resultado;
    }

    private void adicionarGradeAtalhosHome(LinearLayout raiz, String titulo, List<ModuloHome> modulos) {
        TextView heading = texto(titulo, 18, true);
        heading.setPadding(dp(2), dp(8), 0, dp(5));
        raiz.addView(heading);
        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        int count = Math.min(4, modulos.size());
        for (int i = 0; i < count; i++) {
            ModuloHome modulo = modulos.get(i);
            LinearLayout tile = new LinearLayout(this);
            tile.setOrientation(LinearLayout.VERTICAL);
            tile.setGravity(Gravity.CENTER);
            tile.setPadding(dp(4), dp(7), dp(4), dp(6));
            tile.setBackground(fundoComBorda(Color.WHITE, Color.rgb(216, 227, 220), 12));
            TextView icon = texto(iconeModulo(modulo.titulo), 25, true);
            icon.setGravity(Gravity.CENTER);
            icon.setPadding(0, 0, 0, 0);
            TextView label = texto(tituloCurtoAtalho(modulo.titulo), 11, true);
            label.setTextColor(Color.rgb(31, 41, 55));
            label.setGravity(Gravity.CENTER);
            label.setPadding(0, 0, 0, 0);
            label.setMaxLines(2);
            label.setEllipsize(android.text.TextUtils.TruncateAt.END);
            tile.addView(icon);
            tile.addView(label);
            tile.setContentDescription(modulo.titulo);
            tile.setOnClickListener(v -> modulo.acao.run());
            aplicarFeedbackToque(tile);
            LinearLayout.LayoutParams item = new LinearLayout.LayoutParams(0, dp(80), 1);
            item.setMargins(i == 0 ? 0 : dp(5), 0, i == count - 1 ? 0 : dp(1), dp(6));
            row.addView(tile, item);
        }
        raiz.addView(row);
    }

    private String tituloCurtoAtalho(String titulo) {
        if ("Produtividade".equals(titulo)) return "Equipe";
        if ("Análises".equals(titulo)) return "Vendas";
        return titulo;
    }

    private void renderizarModulosHome(LinearLayout destino, List<ModuloHome> modulos, String consulta) {
        destino.removeAllViews();
        String filtro = semAcento(consulta == null ? "" : consulta.trim()).toLowerCase(new Locale("pt", "BR"));
        String[] categorias = {"Operação", "Análises", "Mais"};
        int encontrados = 0;
        for (String categoria : categorias) {
            List<ModuloHome> visiveis = new ArrayList<>();
            for (ModuloHome modulo : modulos) {
                String textoBusca = semAcento(modulo.titulo + " " + modulo.descricao + " " + modulo.categoria).toLowerCase(new Locale("pt", "BR"));
                if (modulo.categoria.equals(categoria) && (filtro.isEmpty() || textoBusca.contains(filtro))) visiveis.add(modulo);
            }
            if (visiveis.isEmpty()) continue;
            encontrados += visiveis.size();
            TextView tituloCategoria = texto(categoria, 13, true);
            tituloCategoria.setTextColor(COR_TEXTO_SUAVE);
            LinearLayout.LayoutParams tituloParams = new LinearLayout.LayoutParams(-1, -2);
            tituloParams.setMargins(0, dp(6), 0, dp(4));
            destino.addView(tituloCategoria, tituloParams);
            int larguraTela = getResources().getConfiguration().screenWidthDp;
            int colunas = larguraTela >= 900 ? 3 : (larguraTela >= 360 ? 2 : 1);
            for (int i = 0; i < visiveis.size(); i += colunas) {
                LinearLayout linha = new LinearLayout(this);
                linha.setOrientation(LinearLayout.HORIZONTAL);
                for (int coluna = 0; coluna < colunas && i + coluna < visiveis.size(); coluna++) {
                    ModuloHome modulo = visiveis.get(i + coluna);
                    LinearLayout.LayoutParams itemParams = new LinearLayout.LayoutParams(0, dp(206), 1);
                    itemParams.setMargins(coluna == 0 ? 0 : dp(6), dp(4), coluna == 0 && colunas == 2 ? dp(6) : 0, dp(4));
                    linha.addView(cartaoModuloHome(modulo), itemParams);
                }
                if (colunas == 2 && visiveis.size() % 2 == 1 && i + 1 >= visiveis.size()) {
                    linha.addView(new View(this), new LinearLayout.LayoutParams(0, dp(206), 1));
                }
                destino.addView(linha);
            }
        }
        if (encontrados == 0) {
            TextView vazio = texto("Nenhum módulo encontrado.", 14, false);
            vazio.setGravity(Gravity.CENTER);
            vazio.setPadding(0, dp(20), 0, dp(20));
            destino.addView(vazio);
        }
    }

    private void carregarResumoHome(LinearLayout destino) {
        new Thread(() -> {
            try {
                Calendar agora = Calendar.getInstance();
                JSONArray vendas = buscarSalesApi("", agora.get(Calendar.YEAR), agora.get(Calendar.MONTH) + 1, 1000);
                JSONObject financeiro = buscarObjetoApi("/api/boletos/summary");
                double total = 0; int entregues = 0;
                Calendar hoje = Calendar.getInstance();
                Calendar inicioGrafico = (Calendar) hoje.clone(); inicioGrafico.add(Calendar.DAY_OF_YEAR, -6);
                Map<String, Double> vendasPorDia = new LinkedHashMap<>();
                SimpleDateFormat chaveDia = new SimpleDateFormat("yyyy-MM-dd", Locale.US);
                Calendar diaCursor = (Calendar) inicioGrafico.clone();
                while (!diaCursor.after(hoje)) { vendasPorDia.put(chaveDia.format(diaCursor.getTime()), 0d); diaCursor.add(Calendar.DAY_OF_YEAR, 1); }
                for (int i = 0; i < vendas.length(); i++) {
                    JSONObject venda = vendas.optJSONObject(i);
                    if (venda == null || "AVARIA".equalsIgnoreCase(venda.optString("sale_type"))) continue;
                    total += venda.optDouble("total", 0);
                    String dataVenda = venda.optString("sale_date", "").trim();
                    if (vendasPorDia.containsKey(dataVenda)) vendasPorDia.put(dataVenda, vendasPorDia.get(dataVenda) + venda.optDouble("total", 0));
                    if ("sim".equalsIgnoreCase(venda.optString("delivered", "")) || "true".equalsIgnoreCase(venda.optString("delivered", ""))) entregues++;
                }
                Calendar anterior = (Calendar) agora.clone(); anterior.add(Calendar.MONTH, -1);
                if (inicioGrafico.get(Calendar.MONTH) != agora.get(Calendar.MONTH)) {
                    JSONArray vendasAnteriores = buscarSalesApi("", anterior.get(Calendar.YEAR), anterior.get(Calendar.MONTH) + 1, 1000);
                    for (int i = 0; i < vendasAnteriores.length(); i++) {
                        JSONObject venda = vendasAnteriores.optJSONObject(i);
                        if (venda == null || "AVARIA".equalsIgnoreCase(venda.optString("sale_type"))) continue;
                        String dataVenda = venda.optString("sale_date", "").trim();
                        if (vendasPorDia.containsKey(dataVenda)) vendasPorDia.put(dataVenda, vendasPorDia.get(dataVenda) + venda.optDouble("total", 0));
                    }
                }
                double totalFinal = total; int entreguesFinal = entregues;
                List<String> rotulosGrafico = new ArrayList<>(); List<Double> valoresGrafico = new ArrayList<>();
                for (Map.Entry<String, Double> item : vendasPorDia.entrySet()) { rotulosGrafico.add(dataCurta(item.getKey())); valoresGrafico.add(item.getValue()); }
                runOnUiThread(() -> {
                    destino.removeAllViews(); destino.setOrientation(LinearLayout.VERTICAL); destino.setVisibility(View.VISIBLE);
                    destino.addView(linhaKpis(cardIndicador("Vendas no mês", moeda.format(totalFinal), "Dados atuais do ERP", Color.rgb(21, 101, 52)),
                        cardIndicador("Entregas", String.valueOf(entreguesFinal), "Notas entregues", Color.rgb(37, 99, 235))));
                    destino.addView(cardIndicador("A receber", moeda.format(financeiro.optDouble("total_pendente", 0)), "Cobranças em aberto", Color.rgb(202, 138, 4)));
                    destino.addView(graficoLinhaAnimado("Evolução de vendas · últimos 7 dias", rotulosGrafico, valoresGrafico, Color.rgb(21, 128, 61), 0));
                });
            } catch (Exception ignored) { runOnUiThread(() -> destino.setVisibility(View.GONE)); }
        }).start();
    }

    private View cartaoModuloHome(ModuloHome modulo) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setGravity(Gravity.TOP);
        card.setMinimumHeight(dp(206));
        card.setPadding(dp(15), dp(13), dp(15), dp(12));
        card.setBackground(fundoCardModulo(modulo.cor));

        TextView icone = new TextView(this);
        icone.setText(iconeModulo(modulo.titulo));
        icone.setTextSize(23);
        icone.setGravity(Gravity.CENTER);
        icone.setContentDescription("Ícone de " + modulo.titulo);
        icone.setBackground(fundoComBorda(Color.rgb(232, 243, 235), Color.rgb(209, 227, 215), 11));
        LinearLayout.LayoutParams iconeParams = new LinearLayout.LayoutParams(dp(50), dp(48));
        iconeParams.setMargins(0, 0, 0, dp(10));
        card.addView(icone, iconeParams);

        LinearLayout textos = coluna();
        textos.setPadding(0, 0, 0, 0);
        TextView titulo = texto(modulo.titulo, 17, true);
        titulo.setMaxLines(2);
        titulo.setEllipsize(android.text.TextUtils.TruncateAt.END);
        titulo.setPadding(0, 0, 0, 0);
        LinearLayout.LayoutParams tituloParams = new LinearLayout.LayoutParams(-1, dp(44));
        tituloParams.setMargins(0, 0, 0, dp(4));
        textos.addView(titulo, tituloParams);
        TextView descricao = texto(modulo.descricao, 13, false);
        descricao.setMaxLines(2);
        descricao.setEllipsize(android.text.TextUtils.TruncateAt.END);
        descricao.setPadding(0, 0, 0, 0);
        textos.addView(descricao, new LinearLayout.LayoutParams(-1, dp(38)));
        card.addView(textos, new LinearLayout.LayoutParams(-1, -2));
        View espacoAcao = new View(this);
        card.addView(espacoAcao, new LinearLayout.LayoutParams(-1, 0, 1));
        TextView seta = texto("Abrir  ›", 13, true);
        seta.setTextColor(modulo.cor);
        seta.setGravity(Gravity.END);
        seta.setPadding(0, 0, 0, 0);
        card.addView(seta, new LinearLayout.LayoutParams(-1, dp(24)));
        card.setOnClickListener(v -> modulo.acao.run());
        card.setFocusable(true);
        aplicarFeedbackToque(card);
        return card;
    }

    private String iconeModulo(String titulo) {
        switch (titulo) {
            case "Entregas": return "🚚";
            case "Vale": return "✍️";
            case "Dados dos vales": return "🧾";
            case "Estoque": return "📦";
            case "Boletos": return "💰";
            case "Projeção": return "📈";
            case "Avarias": return "⚠️";
            case "Produtividade": return "👥";
            case "Clientes": return "🤝";
            case "Consolidado": return "📊";
            case "Análises": return "📉";
            case "Produtos": return "🏷️";
            case "Notificações": return "🔔";
            case "Sincronização ERP": return "🔄";
            default: return "⬇️";
        }
    }

    private View botaoModulo(String titulo, String descricao, int cor, Runnable acao) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.HORIZONTAL);
        card.setGravity(Gravity.CENTER_VERTICAL);
        card.setPadding(dp(14), dp(10), dp(14), dp(10));
        card.setBackground(fundoCardModulo(cor));
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-1, dp(78));
        params.setMargins(0, dp(7), 0, dp(7));
        card.setLayoutParams(params);
        TextView marca = texto("›", 24, true);
        marca.setTextColor(cor);
        marca.setGravity(Gravity.CENTER);
        LinearLayout.LayoutParams marcaParams = new LinearLayout.LayoutParams(dp(36), dp(36));
        marcaParams.setMargins(0, 0, dp(12), 0);
        marca.setBackground(fundoComBorda(Color.rgb(232, 243, 235), Color.rgb(209, 227, 215), 12));
        card.addView(marca, marcaParams);
        LinearLayout textos = coluna();
        TextView t = texto(titulo, 16, true);
        t.setTextColor(Color.rgb(31, 41, 55));
        t.setGravity(Gravity.START);
        TextView d = texto(descricao, 12, false);
        d.setTextColor(Color.rgb(75, 85, 99));
        d.setGravity(Gravity.START);
        d.setMaxLines(2);
        textos.addView(t);
        textos.addView(d);
        card.addView(textos, new LinearLayout.LayoutParams(0, -2, 1));
        TextView abrir = texto("Abrir", 11, true);
        abrir.setTextColor(cor);
        card.addView(abrir);
        card.setOnClickListener(v -> acao.run());
        card.setElevation(dp(5));
        aplicarFeedbackToque(card);
        return card;
    }

    private View linhaModulos(View esquerda, View direita) {
        LinearLayout linha = new LinearLayout(this);
        linha.setOrientation(LinearLayout.HORIZONTAL);
        LinearLayout.LayoutParams linhaParams = new LinearLayout.LayoutParams(-1, dp(106));
        linhaParams.setMargins(0, dp(6), 0, dp(6));
        linha.setLayoutParams(linhaParams);
        LinearLayout.LayoutParams esquerdaParams = new LinearLayout.LayoutParams(0, -1, 1);
        esquerdaParams.setMargins(0, 0, dp(6), 0);
        LinearLayout.LayoutParams direitaParams = new LinearLayout.LayoutParams(0, -1, 1);
        direitaParams.setMargins(dp(6), 0, 0, 0);
        linha.addView(esquerda, esquerdaParams);
        linha.addView(direita, direitaParams);
        return linha;
    }

    private View espacoModuloVazio() {
        View v = new View(this);
        v.setVisibility(View.INVISIBLE);
        return v;
    }

    private void abrirModuloVale() {
        temaEscuroAtivo = true;
        telaAtual = "vale";
        esconderTeclado();
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(COR_FUNDO_ESCURO);
        LinearLayout raiz = coluna();
        raiz.setBackgroundColor(COR_FUNDO_ESCURO);
        raiz.setPadding(dp(18), dp(18), dp(18), dp(28));
        scroll.addView(raiz);

        LinearLayout cabecalho = new LinearLayout(this);
        cabecalho.setOrientation(LinearLayout.HORIZONTAL);
        cabecalho.setGravity(Gravity.CENTER_VERTICAL);
        cabecalho.setPadding(0, 0, 0, dp(10));
        Button home = botao("← Home", Color.rgb(37, 99, 235));
        home.setTextSize(13);
        home.setOnClickListener(v -> confirmarSaidaVale());
        cabecalho.addView(home, new LinearLayout.LayoutParams(dp(96), dp(46)));
        TextView titulo = texto("Vale", 26, true);
        titulo.setGravity(Gravity.CENTER_VERTICAL);
        LinearLayout.LayoutParams tituloParams = new LinearLayout.LayoutParams(0, dp(46), 1);
        tituloParams.setMargins(dp(10), 0, 0, 0);
        cabecalho.addView(titulo, tituloParams);
        raiz.addView(cabecalho);

        TextView subtitulo = texto("Registre o valor solicitado e assine na tela.", 14, false);
        subtitulo.setGravity(Gravity.CENTER_HORIZONTAL);
        subtitulo.setPadding(0, 0, 0, dp(12));
        raiz.addView(subtitulo);

        LinearLayout dados = coluna();
        dados.setPadding(dp(14), dp(12), dp(14), dp(12));
        dados.setBackground(fundoCardEscuro(Color.rgb(234, 179, 8)));
        LinearLayout.LayoutParams dadosParams = new LinearLayout.LayoutParams(-1, -2);
        dadosParams.setMargins(0, dp(6), 0, dp(8));
        raiz.addView(dados, dadosParams);

        dados.addView(texto("Nome do solicitante", 13, false));
        valeSolicitante = campo("Digite o nome do funcionario", InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_CAP_WORDS);
        dados.addView(valeSolicitante);
        dados.addView(texto("Valor solicitado", 13, false));
        valeValor = campo("R$ 0,00", InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_FLAG_DECIMAL);
        valeValor.setKeyListener(DigitsKeyListener.getInstance("0123456789,."));
        dados.addView(valeValor);
        dados.addView(texto("Data", 13, false));
        valeData = campo("Data", InputType.TYPE_CLASS_DATETIME);
        valeData.setFocusable(false);
        valeData.setText(new SimpleDateFormat("dd/MM/yyyy", new Locale("pt", "BR")).format(Calendar.getInstance().getTime()));
        valeData.setOnClickListener(v -> escolherDataVale());
        dados.addView(valeData);

        LinearLayout assinaturaCard = coluna();
        assinaturaCard.setPadding(dp(14), dp(12), dp(14), dp(12));
        assinaturaCard.setBackground(fundoCardEscuro(Color.rgb(148, 163, 184)));
        LinearLayout.LayoutParams assinaturaParams = new LinearLayout.LayoutParams(-1, -2);
        assinaturaParams.setMargins(0, dp(6), 0, dp(8));
        raiz.addView(assinaturaCard, assinaturaParams);
        assinaturaCard.addView(texto("Assinatura do solicitante", 18, true));
        assinaturaCard.addView(texto("Assine abaixo usando o dedo.", 14, false));
        valeAssinatura = new SignatureView(this);
        LinearLayout.LayoutParams sigParams = new LinearLayout.LayoutParams(-1, dp(230));
        sigParams.setMargins(0, dp(10), 0, dp(8));
        assinaturaCard.addView(valeAssinatura, sigParams);

        Button limpar = botao("Limpar assinatura", Color.rgb(107, 114, 128));
        limpar.setOnClickListener(v -> limparAssinaturaVale());
        raiz.addView(limpar);

        Button salvar = botao("Salvar vale", Color.rgb(21, 128, 61));
        salvar.setOnClickListener(v -> salvarVale(salvar));
        raiz.addView(salvar);

        Button cancelar = botao("Cancelar", Color.rgb(185, 28, 28));
        cancelar.setOnClickListener(v -> confirmarSaidaVale());
        raiz.addView(cancelar);

        setContentView(scroll);
    }

    private void escolherDataVale() {
        Calendar c = Calendar.getInstance();
        try {
            String d = valeData.getText().toString();
            if (d.length() == 10) {
                c.set(Calendar.DAY_OF_MONTH, Integer.parseInt(d.substring(0, 2)));
                c.set(Calendar.MONTH, Integer.parseInt(d.substring(3, 5)) - 1);
                c.set(Calendar.YEAR, Integer.parseInt(d.substring(6, 10)));
            }
        } catch (Exception ignored) { }
        new DatePickerDialog(this, (v, a, m, d) -> valeData.setText(String.format(new Locale("pt", "BR"), "%02d/%02d/%04d", d, m + 1, a)), c.get(Calendar.YEAR), c.get(Calendar.MONTH), c.get(Calendar.DAY_OF_MONTH)).show();
    }

    private void limparAssinaturaVale() {
        if (valeAssinatura == null || valeAssinatura.isEmpty()) return;
        new AlertDialog.Builder(this)
            .setTitle("Limpar assinatura?")
            .setMessage("A assinatura desenhada será apagada.")
            .setNegativeButton("Cancelar", null)
            .setPositiveButton("Limpar", (d, w) -> valeAssinatura.clear())
            .show();
    }

    private boolean valeTemDados() {
        boolean temValor = valeValor != null && !valeValor.getText().toString().trim().isEmpty();
        boolean temSolicitante = valeSolicitante != null && !valeSolicitante.getText().toString().trim().isEmpty();
        boolean temAssinatura = valeAssinatura != null && !valeAssinatura.isEmpty();
        return temSolicitante || temValor || temAssinatura;
    }

    private void confirmarSaidaVale() {
        if (!valeTemDados()) {
            mostrarHomeModulos();
            return;
        }
        new AlertDialog.Builder(this)
            .setTitle("Descartar vale?")
            .setMessage("Existe valor ou assinatura preenchida. Deseja sair sem salvar?")
            .setNegativeButton("Continuar editando", null)
            .setPositiveButton("Descartar", (d, w) -> mostrarHomeModulos())
            .show();
    }

    private void salvarVale(Button salvar) {
        String valorTexto = valeValor == null ? "" : valeValor.getText().toString().trim();
        double amount = parseMoedaBR(valorTexto);
        String dataTexto = valeData == null ? "" : valeData.getText().toString().trim();
        String solicitanteNome = valeSolicitante == null ? "" : limparNomeSolicitante(valeSolicitante.getText().toString());
        String username = usernameRegistradorVale();
        String nomeRegistrador = nomeRegistradorVale();
        if (solicitanteNome.isEmpty()) { aviso("Informe o nome do solicitante."); return; }
        if (valorTexto.isEmpty()) { aviso("Informe o valor solicitado."); return; }
        if (amount <= 0) { aviso("O valor deve ser maior que zero."); return; }
        if (dataTexto.isEmpty()) { aviso("Informe a data."); return; }
        if (valeAssinatura == null || valeAssinatura.isEmpty()) { aviso("Faca a assinatura antes de salvar."); return; }
        if (username.isEmpty() && nomeRegistrador.isEmpty()) { aviso("Nao foi possivel identificar o usuario registrador."); return; }
        if (tokenSistema().isEmpty()) { aviso("Sessao expirada. Faca login novamente."); return; }
        salvar.setEnabled(false);
        salvar.setText("Salvando...");
        new Thread(() -> {
            String clientId = UUID.randomUUID().toString();
            String assinatura = "";
            try {
                assinatura = assinaturaValeBase64();
                inserirValeLocalSeNaoExiste(clientId, solicitanteNome, amount, dataApiBR(dataTexto), assinatura, username, nomeRegistrador, "pendente_de_sincronizacao", "");
                JSONObject resposta = enviarValeApi(clientId, solicitanteNome, amount, dataApiBR(dataTexto), assinatura);
                String id = "";
                JSONObject vale = resposta.optJSONObject("vale");
                if (vale != null) id = vale.optString("id", "");
                atualizarValeSincronizado(clientId, id);
                String mensagem = "Vale salvo com sucesso para " + solicitanteNome + "."
                    + "\nValor: " + moeda.format(amount)
                    + "\nData: " + dataTexto
                    + (id.isEmpty() ? "" : "\nID: " + id)
                    + "\n\nDeseja registrar outro vale?";
                runOnUiThread(() -> {
                    if (valeAssinatura != null) valeAssinatura.clear();
                    new AlertDialog.Builder(this)
                        .setTitle("Vale salvo")
                        .setMessage(mensagem)
                        .setNegativeButton("Voltar para Home", (d, w) -> mostrarHomeModulos())
                        .setPositiveButton("Novo vale", (d, w) -> abrirModuloVale())
                        .show();
                });
            } catch (Exception e) {
                if (!assinatura.isEmpty()) {
                    try {
                        inserirValeLocalSeNaoExiste(clientId, solicitanteNome, amount, dataApiBR(dataTexto), assinatura, username, nomeRegistrador, "pendente_de_sincronizacao", "");
                    } catch (Exception ignored) { }
                }
                runOnUiThread(() -> {
                    salvar.setEnabled(true);
                    salvar.setText("Salvar vale");
                    new AlertDialog.Builder(this)
                        .setTitle("Vale salvo no aparelho")
                        .setMessage("O vale foi salvo no aparelho, mas ainda nao foi sincronizado com o servidor.\n\nO app tentara novamente quando validar a sessao.\n\nDetalhe: " + mensagemErroSimples(e))
                        .setPositiveButton("OK", null)
                        .show();
                });
            }
        }).start();
    }

    private String usernameRegistradorVale() {
        return authPrefs().getString("username", "").trim();
    }

    private String nomeRegistradorVale() {
        String nome = authPrefs().getString("full_name", "").trim();
        if (!nome.isEmpty()) return nome;
        return usernameRegistradorVale();
    }

    private JSONObject enviarValeApi(String clientId, String solicitanteNome, double amount, String requestDate, String signatureBase64) throws Exception {
        JSONObject body = new JSONObject();
        body.put("client_id", clientId);
        body.put("solicitante_nome", solicitanteNome);
        body.put("amount", amount);
        body.put("request_date", requestDate);
        body.put("signature_png_base64", signatureBase64);
        body.put("signature_format", "png");
        body.put("source", "android_app");
        byte[] conteudo = body.toString().getBytes("UTF-8");
        HttpURLConnection conexao = null;
        try {
            conexao = (HttpURLConnection) new URL(VALES_URL).openConnection();
            conexao.setRequestMethod("POST");
            conexao.setDoOutput(true);
            conexao.setConnectTimeout(12000);
            conexao.setReadTimeout(25000);
            conexao.setRequestProperty("Content-Type", "application/json; charset=UTF-8");
            conexao.setRequestProperty("Accept", "application/json");
            conexao.setRequestProperty("x-token", tokenSistema());
            conexao.setFixedLengthStreamingMode(conteudo.length);
            try (java.io.OutputStream saida = conexao.getOutputStream()) { saida.write(conteudo); }
            int status = conexao.getResponseCode();
            byte[] resposta = lerFluxo(status >= 200 && status < 300 ? conexao.getInputStream() : conexao.getErrorStream());
            String texto = new String(resposta, "UTF-8");
            if (status == 401 || status == 403) throw new Exception("Sessao expirada. Faca login novamente.");
            if (status < 200 || status >= 300) throw new Exception(texto.isEmpty() ? "Endpoint /api/mobile/vales ainda nao disponivel. Erro " + status : texto);
            return texto.isEmpty() ? new JSONObject().put("success", true) : new JSONObject(texto);
        } finally {
            if (conexao != null) conexao.disconnect();
        }
    }

    private String assinaturaValeBase64() throws Exception {
        Bitmap bmp = valeAssinatura.toBitmap();
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        bmp.compress(Bitmap.CompressFormat.PNG, 100, out);
        return "data:image/png;base64," + Base64.encodeToString(out.toByteArray(), Base64.NO_WRAP);
    }

    private ValesDatabase valesDb() {
        if (valesDatabase == null) valesDatabase = new ValesDatabase(this);
        return valesDatabase;
    }

    private String limparNomeSolicitante(String nome) {
        if (nome == null) return "";
        return nome.trim().replaceAll("\\s+", " ");
    }

    private String chaveSolicitante(String nome) {
        return semAcento(limparNomeSolicitante(nome)).toLowerCase(new Locale("pt", "BR"));
    }

    private void inserirValeLocalSeNaoExiste(String clientId, String solicitanteNome, double amount, String requestDate, String assinatura, String username, String registradorNome, String status, String remoteId) {
        SQLiteDatabase db = valesDb().getWritableDatabase();
        Cursor c = null;
        try {
            c = db.query("vales", new String[]{"client_id"}, "client_id=?", new String[]{clientId}, null, null, null);
            if (c.moveToFirst()) return;
        } finally {
            if (c != null) c.close();
        }
        ContentValues v = new ContentValues();
        v.put("client_id", clientId);
        v.put("remote_id", remoteId == null ? "" : remoteId);
        v.put("solicitante_nome", limparNomeSolicitante(solicitanteNome));
        v.put("solicitante_key", chaveSolicitante(solicitanteNome));
        v.put("amount", amount);
        v.put("request_date", requestDate);
        v.put("signature_png_base64", assinatura);
        v.put("signature_format", "png");
        v.put("registered_by_username", username == null ? "" : username);
        v.put("registered_by_name", registradorNome == null ? "" : registradorNome);
        v.put("status", status == null ? "pendente_de_sincronizacao" : status);
        v.put("created_at", System.currentTimeMillis());
        v.put("synced_at", 0L);
        db.insertWithOnConflict("vales", null, v, SQLiteDatabase.CONFLICT_IGNORE);
    }

    private void atualizarValeSincronizado(String clientId, String remoteId) {
        ContentValues v = new ContentValues();
        v.put("status", "sincronizado");
        v.put("remote_id", remoteId == null ? "" : remoteId);
        v.put("synced_at", System.currentTimeMillis());
        valesDb().getWritableDatabase().update("vales", v, "client_id=?", new String[]{clientId});
    }

    private void sincronizarValesPendentesSilencioso() {
        if (tokenSistema().isEmpty()) return;
        new Thread(() -> {
            List<ValeRegistro> pendentes = listarValesPendentes();
            for (ValeRegistro r : pendentes) {
                try {
                    JSONObject resposta = enviarValeApi(r.clientId, r.solicitanteNome, r.amount, r.requestDate, r.assinaturaBase64);
                    String id = "";
                    JSONObject vale = resposta.optJSONObject("vale");
                    if (vale != null) id = vale.optString("id", "");
                    atualizarValeSincronizado(r.clientId, id);
                } catch (Exception ignored) {
                    return;
                }
            }
        }).start();
    }

    private List<ValeRegistro> listarValesPendentes() {
        List<ValeRegistro> lista = new ArrayList<>();
        Cursor c = null;
        try {
            c = valesDb().getReadableDatabase().query("vales", null, "status=?", new String[]{"pendente_de_sincronizacao"}, null, null, "created_at ASC");
            while (c.moveToNext()) lista.add(valeRegistroCursor(c));
        } finally {
            if (c != null) c.close();
        }
        return lista;
    }

    private void abrirModuloDadosVales(String buscaInicial) {
        temaEscuroAtivo = true;
        telaAtual = "dados_vales";
        esconderTeclado();
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(COR_FUNDO_ESCURO);
        LinearLayout raiz = coluna();
        raiz.setBackgroundColor(COR_FUNDO_ESCURO);
        raiz.setPadding(dp(18), dp(18), dp(18), dp(28));
        scroll.addView(raiz);
        adicionarCabecalhoModulo(raiz, "Dados dos vales", "Consulte os vales por solicitante.");

        EditText busca = campo("Buscar solicitante", InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS);
        busca.setText(buscaInicial == null ? "" : buscaInicial);
        raiz.addView(busca);
        LinearLayout lista = coluna();
        raiz.addView(lista);
        Button atualizar = botao("Atualizar lista", Color.rgb(14, 165, 233));
        atualizar.setOnClickListener(v -> carregarDadosVales(busca.getText().toString(), lista));
        raiz.addView(atualizar);
        Button voltar = botao("Voltar para Home", Color.rgb(37, 99, 235));
        voltar.setOnClickListener(v -> mostrarHomeModulos());
        raiz.addView(voltar);
        setContentView(scroll);
        busca.setOnEditorActionListener((v, actionId, event) -> {
            carregarDadosVales(busca.getText().toString(), lista);
            esconderTeclado();
            return true;
        });
        carregarDadosVales(busca.getText().toString(), lista);
    }

    private void carregarDadosVales(String busca, LinearLayout lista) {
        lista.removeAllViews();
        String filtro = chaveSolicitante(busca);
        List<ValeResumo> resumos = listarResumoVales(filtro);
        if (resumos.isEmpty()) {
            lista.addView(cardLeitura("Nenhum vale encontrado", "Salve um vale para aparecer aqui.", "", "", Color.rgb(21, 101, 52)));
            return;
        }
        for (ValeResumo r : resumos) {
            String linhaQtd = r.quantidade == 1 ? "1 solicitacao" : r.quantidade + " solicitacoes";
            View card = cardLeitura(r.nomeExibicao, linhaQtd, "Total solicitado: " + moeda.format(r.total), "Ultima solicitacao: " + dataBR(r.ultimaData), Color.rgb(21, 101, 52));
            card.setOnClickListener(v -> abrirDetalheSolicitanteVales(r.chave, r.nomeExibicao));
            aplicarFeedbackToque(card);
            lista.addView(card);
        }
    }

    private List<ValeResumo> listarResumoVales(String filtroKey) {
        LinkedHashMap<String, ValeResumo> mapa = new LinkedHashMap<>();
        Cursor c = null;
        try {
            c = valesDb().getReadableDatabase().query("vales", null, null, null, null, null, "request_date DESC, created_at DESC");
            while (c.moveToNext()) {
                ValeRegistro r = valeRegistroCursor(c);
                if (filtroKey != null && !filtroKey.isEmpty() && !r.solicitanteKey.contains(filtroKey)) continue;
                ValeResumo resumo = mapa.get(r.solicitanteKey);
                if (resumo == null) {
                    resumo = new ValeResumo();
                    resumo.chave = r.solicitanteKey;
                    resumo.nomeExibicao = r.solicitanteNome;
                    resumo.primeiraData = r.requestDate;
                    resumo.ultimaData = r.requestDate;
                    mapa.put(r.solicitanteKey, resumo);
                } else if (r.solicitanteNome.length() > resumo.nomeExibicao.length()) {
                    resumo.nomeExibicao = r.solicitanteNome;
                }
                resumo.quantidade++;
                resumo.total += r.amount;
                if (r.requestDate.compareTo(resumo.ultimaData) > 0) resumo.ultimaData = r.requestDate;
                if (r.requestDate.compareTo(resumo.primeiraData) < 0) resumo.primeiraData = r.requestDate;
            }
        } finally {
            if (c != null) c.close();
        }
        return new ArrayList<>(mapa.values());
    }

    private void abrirDetalheSolicitanteVales(String solicitanteKey, String nomeExibicao) {
        temaEscuroAtivo = true;
        telaAtual = "dados_vales_detalhe";
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(COR_FUNDO_ESCURO);
        LinearLayout raiz = coluna();
        raiz.setBackgroundColor(COR_FUNDO_ESCURO);
        raiz.setPadding(dp(18), dp(18), dp(18), dp(28));
        scroll.addView(raiz);
        adicionarCabecalhoModulo(raiz, "Solicitacoes de " + nomeExibicao, "Valores e assinaturas deste solicitante.");
        List<ValeRegistro> vales = listarValesPorSolicitante(solicitanteKey);
        double total = 0;
        String primeira = "", ultima = "";
        for (ValeRegistro v : vales) {
            total += v.amount;
            if (primeira.isEmpty() || v.requestDate.compareTo(primeira) < 0) primeira = v.requestDate;
            if (ultima.isEmpty() || v.requestDate.compareTo(ultima) > 0) ultima = v.requestDate;
        }
        double media = total / Math.max(1, vales.size());
        raiz.addView(cardLeitura("Resumo", "Solicitacoes: " + vales.size(), "Total: " + moeda.format(total) + " • Media: " + moeda.format(media), "Periodo: " + dataBR(primeira) + " ate " + dataBR(ultima), Color.rgb(21, 101, 52)));
        for (ValeRegistro v : vales) {
            LinearLayout card = coluna();
            card.setPadding(dp(14), dp(12), dp(14), dp(12));
            card.setBackground(fundoCardEscuro("sincronizado".equals(v.status) ? Color.rgb(34, 197, 94) : Color.rgb(234, 179, 8)));
            LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-1, -2);
            params.setMargins(0, dp(6), 0, dp(8));
            raiz.addView(card, params);
            card.addView(texto("Valor: " + moeda.format(v.amount), 17, true));
            card.addView(texto("Data: " + dataBR(v.requestDate), 14, false));
            card.addView(texto("Status: " + nomeStatusVale(v.status), 14, false));
            card.addView(texto("Assinatura: disponivel", 14, false));
            if (!v.registeredByName.isEmpty() || !v.registeredByUsername.isEmpty()) {
                card.addView(texto("Registrado por: " + (!v.registeredByName.isEmpty() ? v.registeredByName : v.registeredByUsername), 13, false));
            }
            Button ver = botao("Ver assinatura", Color.rgb(14, 165, 233));
            ver.setOnClickListener(btn -> mostrarAssinaturaVale(v));
            card.addView(ver);
        }
        Button voltar = botao("Voltar para Dados", Color.rgb(14, 165, 233));
        voltar.setOnClickListener(v -> abrirModuloDadosVales(nomeExibicao));
        raiz.addView(voltar);
        Button home = botao("Voltar para Home", Color.rgb(37, 99, 235));
        home.setOnClickListener(v -> mostrarHomeModulos());
        raiz.addView(home);
        setContentView(scroll);
    }

    private List<ValeRegistro> listarValesPorSolicitante(String solicitanteKey) {
        List<ValeRegistro> lista = new ArrayList<>();
        Cursor c = null;
        try {
            c = valesDb().getReadableDatabase().query("vales", null, "solicitante_key=?", new String[]{solicitanteKey}, null, null, "request_date DESC, created_at DESC");
            while (c.moveToNext()) lista.add(valeRegistroCursor(c));
        } finally {
            if (c != null) c.close();
        }
        return lista;
    }

    private ValeRegistro valeRegistroCursor(Cursor c) {
        ValeRegistro r = new ValeRegistro();
        r.clientId = c.getString(c.getColumnIndexOrThrow("client_id"));
        r.remoteId = c.getString(c.getColumnIndexOrThrow("remote_id"));
        r.solicitanteNome = c.getString(c.getColumnIndexOrThrow("solicitante_nome"));
        r.solicitanteKey = c.getString(c.getColumnIndexOrThrow("solicitante_key"));
        r.amount = c.getDouble(c.getColumnIndexOrThrow("amount"));
        r.requestDate = c.getString(c.getColumnIndexOrThrow("request_date"));
        r.assinaturaBase64 = c.getString(c.getColumnIndexOrThrow("signature_png_base64"));
        r.signatureFormat = c.getString(c.getColumnIndexOrThrow("signature_format"));
        r.registeredByUsername = c.getString(c.getColumnIndexOrThrow("registered_by_username"));
        r.registeredByName = c.getString(c.getColumnIndexOrThrow("registered_by_name"));
        r.status = c.getString(c.getColumnIndexOrThrow("status"));
        r.createdAt = c.getLong(c.getColumnIndexOrThrow("created_at"));
        return r;
    }

    private String nomeStatusVale(String status) {
        if ("sincronizado".equalsIgnoreCase(status)) return "Sincronizado";
        return "Pendente de sincronizacao";
    }

    private void mostrarAssinaturaVale(ValeRegistro vale) {
        try {
            String raw = vale.assinaturaBase64 == null ? "" : vale.assinaturaBase64;
            int comma = raw.indexOf(',');
            if (comma >= 0) raw = raw.substring(comma + 1);
            byte[] bytes = Base64.decode(raw, Base64.DEFAULT);
            Bitmap bitmap = BitmapFactory.decodeByteArray(bytes, 0, bytes.length);
            if (bitmap == null) throw new Exception("assinatura vazia");
            LinearLayout box = coluna();
            box.setPadding(dp(10), dp(8), dp(10), dp(8));
            TextView info = texto(vale.solicitanteNome + "\nValor: " + moeda.format(vale.amount) + "\nData: " + dataBR(vale.requestDate), 14, false);
            box.addView(info);
            ImageView img = new ImageView(this);
            img.setImageBitmap(bitmap);
            img.setAdjustViewBounds(true);
            img.setBackgroundColor(Color.WHITE);
            box.addView(img, new LinearLayout.LayoutParams(-1, dp(260)));
            new AlertDialog.Builder(this)
                .setTitle("Assinatura do solicitante")
                .setView(box)
                .setPositiveButton("Fechar", null)
                .show();
        } catch (Exception e) {
            aviso("Nao foi possivel abrir a assinatura.");
        }
    }

    private double parseMoedaBR(String texto) {
        if (texto == null) return 0;
        String limpo = texto.replace("R$", "").replace(" ", "").trim();
        if (limpo.contains(",") && limpo.contains(".")) limpo = limpo.replace(".", "").replace(",", ".");
        else limpo = limpo.replace(",", ".");
        try { return Double.parseDouble(limpo); } catch (Exception e) { return 0; }
    }

    private String dataApiBR(String br) {
        try { return br.substring(6, 10) + "-" + br.substring(3, 5) + "-" + br.substring(0, 2); }
        catch (Exception e) { return br; }
    }

    private void mostrarMenuEntregas() {
        temaEscuroAtivo = true;
        telaAtual = "entregas_menu";
        ScrollView scroll = new ScrollView(this);
        scroll.setBackgroundColor(COR_FUNDO_ESCURO);
        LinearLayout raiz = coluna();
        raiz.setBackgroundColor(COR_FUNDO_ESCURO);
        raiz.setPadding(dp(18), dp(16), dp(18), dp(24));
        scroll.addView(raiz);
        adicionarCabecalhoModulo(raiz, "Entregas", "Pedidos novos e acompanhamento das notas.");
        adicionarBannerModulo(raiz, "CENTRAL DE ENTREGAS", "Escolha como registrar ou acompanhar", "Crie uma nota manualmente, dite o pedido ou confira o andamento das entregas.", Color.rgb(21, 101, 52));
        TextView secao = texto("O que você vai fazer?", 16, true);
        secao.setPadding(0, dp(12), 0, dp(6));
        raiz.addView(secao);
        raiz.addView(botaoModulo("Lançar entrega", "Ditar cliente e produtos por voz", Color.rgb(21, 101, 52), () -> iniciarEntregaPorVoz()));
        raiz.addView(botaoModulo("Acompanhar entregas", "Ver notas pendentes e concluídas", Color.rgb(21, 101, 52), () -> abrirModuloEntregas(false)));
        setContentView(scroll);
    }

    private void iniciarEntregaPorVoz() {
        if (!SpeechRecognizer.isRecognitionAvailable(this)) {
            new AlertDialog.Builder(this).setTitle("Voz indisponível")
                .setMessage("Este celular não tem reconhecimento de voz ativo. Você pode ativar o serviço de voz ou abrir o formulário manual, que continua disponível como alternativa.")
                .setPositiveButton("Abrir formulário manual", (d, w) -> abrirTelaPedido())
                .setNegativeButton("Voltar", (d, w) -> mostrarMenuEntregas()).show();
            return;
        }
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO}, PEDIDO_AUDIO_VOZ);
            return;
        }
        if (!itens.isEmpty()) {
            new AlertDialog.Builder(this).setTitle("Há um pedido em edição")
                .setMessage("Para proteger os produtos já lançados, envie ou limpe esse pedido antes de iniciar a entrega por voz.")
                .setNegativeButton("Voltar", (d, w) -> abrirTelaPedido())
                .setPositiveButton("Manter rascunho", (d, w) -> mostrarMenuEntregas()).show();
            return;
        }
        iniciarSessaoVoz();
    }

    private View cardSaldoEstoque(String nome, String sku, String saldo, int vendas, double quantidade) {
        final int cor, borda;
        if (quantidade <= 0) { cor = Color.rgb(254, 226, 226); borda = Color.rgb(220, 38, 38); }
        else if (quantidade <= 10) { cor = Color.rgb(255, 237, 213); borda = Color.rgb(234, 88, 12); }
        else if (quantidade > 300) { cor = Color.rgb(219, 234, 254); borda = Color.rgb(37, 99, 235); }
        else { cor = Color.rgb(220, 252, 231); borda = Color.rgb(22, 163, 74); }
        LinearLayout card = coluna();
        card.setPadding(dp(14), dp(12), dp(14), dp(12));
        card.setBackground(fundoComBorda(cor, borda, 13));
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(-1, -2); p.setMargins(0, dp(5), 0, dp(5)); card.setLayoutParams(p);
        card.addView(texto(nome, 17, true));
        TextView saldoView = texto(saldo, 20, true); saldoView.setTextColor(borda); saldoView.setPadding(0, dp(4), 0, 0); card.addView(saldoView);
        card.addView(texto("SKU: " + (sku == null || sku.trim().isEmpty() ? "—" : sku), 12, false));
        card.addView(texto(vendas + " venda(s) no histórico", 12, false));
        TextView acao = texto("＋ Toque para adicionar entrada", 12, true);
        acao.setTextColor(Color.rgb(21, 101, 52));
        acao.setPadding(0, dp(5), 0, 0);
        card.addView(acao);
        return card;
    }

    @Override public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == 410) {
            CalendarNotificationReceiver.agendar(this);
            NewTempoCollectionReceiver.agendar(this);
            if (grantResults.length == 0 || grantResults[0] != PackageManager.PERMISSION_GRANTED)
                aviso("Sem essa permissão, o Android não pode mostrar os avisos. Ative notificações do Menina dos Raios nas configurações.");
        }
        if (requestCode == PEDIDO_AUDIO_VOZ) {
            if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) iniciarEntregaPorVoz();
            else new AlertDialog.Builder(this).setTitle("Microfone não autorizado")
                .setMessage("Ative a permissão do microfone para ditar o pedido. Se preferir, o formulário manual continua disponível como alternativa.")
                .setPositiveButton("Formulário manual", (d, w) -> abrirTelaPedido())
                .setNegativeButton("Voltar", (d, w) -> mostrarMenuEntregas()).show();
        }
    }

    private void iniciarSessaoVoz() {
        telaAtual = "entrega_voz";
        carregarProdutos();
        sincronizarCatalogoMonteiro((disponivel, atualizado) -> {
            if (!disponivel) {
                new AlertDialog.Builder(this).setTitle("Lista de produtos indisponível")
                    .setMessage("Não consegui carregar a lista oficial do Monteiro. Conecte o aparelho à internet e tente novamente.")
                    .setPositiveButton("Voltar", (d, w) -> mostrarMenuEntregas()).show();
                return;
            }
            if (!atualizado) aviso("Sem internet: usando a última lista salva do Monteiro.");
            iniciarSessaoVozComCatalogo();
        });
    }

    private void iniciarSessaoVozComCatalogo() {
        temaEscuroAtivo = false;
        telaAtual = "entrega_voz";
        itensVoz.clear();
        itemNovoPendente = null;
        clienteVoz = "";
        dataVoz = new SimpleDateFormat("dd/MM/yyyy", new Locale("pt", "BR")).format(Calendar.getInstance().getTime());
        if (falaVoz == null) {
            falaVoz = new TextToSpeech(this, status -> {
                int idioma = status == TextToSpeech.SUCCESS && falaVoz != null
                    ? falaVoz.setLanguage(new Locale("pt", "BR")) : TextToSpeech.LANG_NOT_SUPPORTED;
                falaPronta = idioma >= TextToSpeech.LANG_AVAILABLE;
                if (falaPronta) falaVoz.setSpeechRate(1.14f);
                montarTelaEntregaVoz();
                iniciarPromptOuRestaurarVoz();
            });
        } else {
            int idioma = falaVoz.setLanguage(new Locale("pt", "BR"));
            falaPronta = idioma >= TextToSpeech.LANG_AVAILABLE;
            if (falaPronta) falaVoz.setSpeechRate(1.14f);
            montarTelaEntregaVoz();
            iniciarPromptOuRestaurarVoz();
        }
    }

    private void iniciarPromptOuRestaurarVoz() {
        if (oferecerRestaurarRascunhoVoz()) return;
        new Handler(Looper.getMainLooper()).postDelayed(
            () -> { if ("entrega_voz".equals(telaAtual) && !escutaVozAtiva) perguntarVoz("cliente", "Qual o cliente?"); }, 1000);
    }

    private boolean oferecerRestaurarRascunhoVoz() {
        String salvo = getSharedPreferences("rascunhos_notas", MODE_PRIVATE).getString("voz", "");
        JSONObject rascunho;
        try { rascunho = salvo.isEmpty() ? null : new JSONObject(salvo); }
        catch (Exception e) { rascunho = null; }
        if (rascunho == null) return false;
        JSONArray lista = rascunho.optJSONArray("items");
        String clienteSalvo = nomeClienteMaiusculo(rascunho.optString("client", ""));
        JSONObject finalRascunho = rascunho;
        new AlertDialog.Builder(this).setTitle("Rascunho de voz recuperado")
            .setMessage("Cliente: " + (clienteSalvo.isEmpty() ? "a confirmar" : clienteSalvo)
                + "\n" + (lista == null ? 0 : lista.length()) + " item(ns). Deseja continuar?")
            .setPositiveButton("Continuar", (d, w) -> restaurarRascunhoVoz(finalRascunho))
            .setNegativeButton("Nova nota", (d, w) -> {
                limparRascunhoVoz();
                clienteVoz = ""; itensVoz.clear(); itemNovoPendente = null;
                dataVoz = new SimpleDateFormat("dd/MM/yyyy", new Locale("pt", "BR")).format(Calendar.getInstance().getTime());
                atualizarListaItensVoz(); atualizarResumoVoz(); perguntarVoz("cliente", "Qual o cliente?");
            })
            .setOnCancelListener(d -> restaurarRascunhoVoz(finalRascunho))
            .show();
        return true;
    }

    private void restaurarRascunhoVoz(JSONObject salvo) {
        clienteVoz = nomeClienteMaiusculo(salvo.optString("client", ""));
        dataVoz = salvo.optString("date", dataVoz);
        itensVoz.clear();
        JSONArray lista = salvo.optJSONArray("items");
        if (lista != null) for (int i = 0; i < lista.length(); i++) {
            JSONObject item = lista.optJSONObject(i);
            if (item != null) itensVoz.add(new ItemInterpretado(item.optString("product"), item.optDouble("measure"),
                item.optString("unit"), item.optBoolean("is_new", false)));
        }
        JSONObject pendente = salvo.optJSONObject("pending_new_item");
        itemNovoPendente = pendente == null ? null : new ItemInterpretado(pendente.optString("product"),
            pendente.optDouble("measure"), pendente.isNull("unit") ? null : pendente.optString("unit"), true);
        atualizarListaItensVoz(); atualizarResumoVoz();
        String etapaSalva = salvo.optString("step", "");
        if ("confirmar_novo_produto".equals(etapaSalva) && itemNovoPendente != null)
            perguntarVoz(etapaSalva, "Não encontrei " + itemNovoPendente.produto + " na lista do Monteiro. É um produto novo?");
        else if ("corrigir_nome_produto".equals(etapaSalva) && itemNovoPendente != null)
            perguntarVoz(etapaSalva, "Diga o nome correto do produto da lista do Monteiro.");
        else if ("unidade_novo_produto".equals(etapaSalva) && itemNovoPendente != null)
            perguntarVoz(etapaSalva, "Qual a unidade? Peso, unidade, caixa, maço ou saco.");
        else if (clienteVoz.isEmpty()) perguntarVoz("cliente", "Qual o cliente?");
        else if (itensVoz.isEmpty()) perguntarProdutoVoz();
        else confirmarProdutosVoz();
    }

    private void guardarRascunhoVoz() {
        if (!"entrega_voz".equals(telaAtual)) return;
        try {
            JSONObject salvo = new JSONObject();
            salvo.put("client", clienteVoz); salvo.put("date", dataVoz);
            salvo.put("step", etapaVoz);
            JSONArray lista = new JSONArray();
            for (ItemInterpretado item : itensVoz) {
                JSONObject produtoSalvo = new JSONObject();
                produtoSalvo.put("product", item.produto); produtoSalvo.put("measure", item.medida);
                produtoSalvo.put("unit", item.unidade); produtoSalvo.put("is_new", item.novo); lista.put(produtoSalvo);
            }
            salvo.put("items", lista);
            if (itemNovoPendente != null) {
                JSONObject pendente = new JSONObject();
                pendente.put("product", itemNovoPendente.produto); pendente.put("measure", itemNovoPendente.medida);
                pendente.put("unit", itemNovoPendente.unidade == null ? JSONObject.NULL : itemNovoPendente.unidade);
                salvo.put("pending_new_item", pendente);
            }
            SharedPreferences.Editor editor = getSharedPreferences("rascunhos_notas", MODE_PRIVATE).edit();
            if (!clienteVoz.isEmpty() || !itensVoz.isEmpty() || itemNovoPendente != null) editor.putString("voz", salvo.toString());
            else editor.remove("voz");
            editor.commit();
        } catch (Exception ignored) { }
    }

    private void limparRascunhoVoz() {
        getSharedPreferences("rascunhos_notas", MODE_PRIVATE).edit().remove("voz").commit();
    }

    private void montarTelaEntregaVoz() {
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(Color.rgb(244, 247, 244));
        vozRaiz = coluna();
        vozRaiz.setBackgroundColor(Color.rgb(244, 247, 244));
        vozRaiz.setPadding(dp(18), dp(18), dp(18), dp(26));
        scroll.addView(vozRaiz);
        adicionarCabecalhoModulo(vozRaiz, "Novo pedido (entrega)", "Informe o cliente e dite os produtos. Revise antes de enviar.");
        LinearLayout etapa = new LinearLayout(this);
        etapa.setGravity(Gravity.CENTER);
        etapa.setPadding(dp(8), dp(10), dp(8), dp(10));
        etapa.setBackground(fundoComBorda(Color.WHITE, Color.rgb(216, 227, 220), 12));
        TextView etapaTexto = texto("CLIENTE    ›    PRODUTOS    ›    REVISAR", 12, true);
        etapaTexto.setTextColor(Color.rgb(21, 101, 52));
        etapa.addView(etapaTexto);
        LinearLayout.LayoutParams etapaParams = new LinearLayout.LayoutParams(-1, -2);
        etapaParams.setMargins(0, 0, 0, dp(10));
        vozRaiz.addView(etapa, etapaParams);
        vozClienteData = texto("Cliente ainda não informado\nData da nota: " + dataVoz, 16, true);
        vozClienteData.setPadding(dp(16), dp(16), dp(16), dp(16));
        vozClienteData.setBackground(fundoComBorda(Color.rgb(240, 248, 242), Color.rgb(205, 225, 209), 12));
        vozRaiz.addView(vozClienteData);
        vozPergunta = texto("Preparando conversa...", 21, true);
        vozPergunta.setTextColor(Color.rgb(20, 33, 46));
        vozPergunta.setGravity(Gravity.CENTER);
        vozPergunta.setPadding(dp(8), dp(16), dp(8), dp(6));
        vozRaiz.addView(vozPergunta);
        vozEstado = texto("Toque no microfone para falar", 15, false);
        vozEstado.setTextColor(Color.rgb(100, 116, 139));
        vozEstado.setGravity(Gravity.CENTER);
        vozRaiz.addView(vozEstado);
        vozMicrofone = botao("🎙  Falar pedido", Color.rgb(21, 101, 52));
        vozMicrofone.setTextSize(20);
        vozMicrofone.setBackground(fundoArredondado(Color.rgb(0, 91, 55), 16));
        vozMicrofone.setContentDescription("Começar a falar o nome do cliente ou os produtos");
        LinearLayout.LayoutParams micParams = new LinearLayout.LayoutParams(-1, dp(68));
        micParams.setMargins(0, dp(10), 0, dp(3));
        vozRaiz.addView(vozMicrofone, micParams);
        vozMicrofone.setOnClickListener(v -> ouvirVoz());
        TextView dicaVoz = texto("Diga o produto e a quantidade em qualquer ordem.", 13, false);
        dicaVoz.setGravity(Gravity.CENTER);
        dicaVoz.setPadding(0, 0, 0, dp(8));
        vozRaiz.addView(dicaVoz);
        LinearLayout respostas = new LinearLayout(this);
        respostas.setOrientation(LinearLayout.HORIZONTAL);
        vozSim = botao("Sim", Color.rgb(21, 128, 61));
        vozNao = botao("Não", Color.rgb(185, 28, 28));
        LinearLayout.LayoutParams resp1 = new LinearLayout.LayoutParams(0, dp(52), 1);
        resp1.setMargins(0, 0, dp(5), 0);
        LinearLayout.LayoutParams resp2 = new LinearLayout.LayoutParams(0, dp(52), 1);
        resp2.setMargins(dp(5), 0, 0, 0);
        respostas.addView(vozSim, resp1);
        respostas.addView(vozNao, resp2);
        vozRaiz.addView(respostas);
        vozSim.setOnClickListener(v -> processarRespostaVoz("sim"));
        vozNao.setOnClickListener(v -> processarRespostaVoz("não"));
        vozSecaoProdutos = texto("Produtos (0)", 18, true);
        vozSecaoProdutos.setPadding(0, dp(16), 0, dp(6));
        vozRaiz.addView(vozSecaoProdutos);
        vozLista = coluna();
        vozRaiz.addView(vozLista);
        Button revisar = botao("Revisar pedido  ›", Color.rgb(0, 91, 55));
        LinearLayout.LayoutParams revisarParams = new LinearLayout.LayoutParams(-1, dp(54));
        revisarParams.setMargins(0, dp(10), 0, dp(6));
        vozRaiz.addView(revisar, revisarParams);
        revisar.setOnClickListener(v -> confirmarProdutosVoz());
        Button editarData = botao("Alterar data", Color.rgb(71, 85, 105));
        editarData.setOnClickListener(v -> escolherDataVoz());
        vozRaiz.addView(editarData);
        Button cancelar = botao("Cancelar e voltar", Color.rgb(100, 116, 139));
        cancelar.setOnClickListener(v -> encerrarEntregaVoz(true));
        vozRaiz.addView(cancelar);
        setContentView(scroll);
        atualizarResumoVoz();
    }

    private void perguntarVoz(String etapa, String pergunta) {
        etapaVoz = etapa;
        guardarRascunhoVoz();
        boolean respostaBinaria = etapa.equals("confirmar_cliente") || etapa.equals("confirmar_data")
            || etapa.equals("proximo_item") || etapa.equals("confirmar_produtos")
            || etapa.equals("enviar") || etapa.equals("mesmo_cliente")
            || etapa.equals("confirmar_novo_produto");
        if (vozSim != null) vozSim.setVisibility(respostaBinaria ? View.VISIBLE : View.GONE);
        if (vozNao != null) vozNao.setVisibility(respostaBinaria ? View.VISIBLE : View.GONE);
        if (vozPergunta != null) vozPergunta.setText(pergunta);
        if (vozEstado != null) vozEstado.setText("Toque no microfone para responder.");
        if (!escutaVozAtiva) falar(pergunta, null);
    }

    private void falar(String frase, Runnable aoTerminar) {
        falarLocal(frase, aoTerminar);
    }

    private void falarLocal(String frase, Runnable aoTerminar) {
        if (!falaPronta || falaVoz == null) {
            if (aoTerminar != null) aoTerminar.run();
            return;
        }
        falaVoz.setSpeechRate(1.14f);
        falaVoz.setOnUtteranceProgressListener(new UtteranceProgressListener() {
            @Override public void onStart(String id) { }
            @Override public void onDone(String id) {
                if (aoTerminar != null) runOnUiThread(aoTerminar);
            }
            @Override public void onError(String id) {
                if (aoTerminar != null) runOnUiThread(aoTerminar);
            }
        });
        falaVoz.speak(frase, TextToSpeech.QUEUE_FLUSH, null, UUID.randomUUID().toString());
    }

    private void ouvirVoz() {
        if (falaVoz != null) falaVoz.stop();
        if (!SpeechRecognizer.isRecognitionAvailable(this)) { aviso("Reconhecimento de voz indisponível neste celular."); return; }
        liberarReconhecedorVoz();
        escutaVozAtiva = true;
        long tentativa = ++tentativaEscutaVoz;
        reconhecedorVoz = SpeechRecognizer.createSpeechRecognizer(this);
        reconhecedorVoz.setRecognitionListener(new RecognitionListener() {
            @Override public void onReadyForSpeech(Bundle params) { runOnUiThread(() -> { if (tentativa == tentativaEscutaVoz && vozEstado != null) vozEstado.setText("Pode falar."); }); }
            @Override public void onBeginningOfSpeech() { runOnUiThread(() -> { if (tentativa == tentativaEscutaVoz && vozEstado != null) vozEstado.setText("Ouvindo..."); }); }
            @Override public void onRmsChanged(float rmsdB) { }
            @Override public void onBufferReceived(byte[] buffer) { }
            @Override public void onEndOfSpeech() { runOnUiThread(() -> { if (tentativa == tentativaEscutaVoz && vozEstado != null) vozEstado.setText("Reconhecendo..."); }); }
            @Override public void onError(int error) { runOnUiThread(() -> {
                if (tentativa != tentativaEscutaVoz) return;
                escutaVozAtiva = false;
                tentativaEscutaVoz++;
                if (vozEstado != null) vozEstado.setText("Não ouvi. Toque para tentar novamente.");
                restaurarMicrofoneVoz();
            }); }
            @Override public void onResults(Bundle results) {
                ArrayList<String> frases = results.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION);
                runOnUiThread(() -> {
                    if (tentativa != tentativaEscutaVoz) return;
                    escutaVozAtiva = false;
                    tentativaEscutaVoz++;
                    restaurarMicrofoneVoz();
                    if (frases != null && !frases.isEmpty()) processarRespostaVoz(frases.get(0));
                });
            }
            @Override public void onPartialResults(Bundle partialResults) { }
            @Override public void onEvent(int eventType, Bundle params) { }
        });
        Intent intent = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, "pt-BR");
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE, "pt-BR");
        intent.putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 3);
        intent.putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, false);
        intent.putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_COMPLETE_SILENCE_LENGTH_MILLIS, 1800L);
        intent.putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_MINIMUM_LENGTH_MILLIS, 300L);
        vozMicrofone.setEnabled(false);
        vozMicrofone.setText("Ouvindo...");
        reconhecedorVoz.startListening(intent);
        new Handler(Looper.getMainLooper()).postDelayed(() -> {
            if (tentativa != tentativaEscutaVoz || !escutaVozAtiva) return;
            escutaVozAtiva = false;
            tentativaEscutaVoz++;
            liberarReconhecedorVoz();
            if (vozEstado != null) vozEstado.setText("Tempo esgotado. Toque para tentar novamente.");
            restaurarMicrofoneVoz();
        }, 30000);
    }

    private void restaurarMicrofoneVoz() {
        if (vozMicrofone != null) { vozMicrofone.setEnabled(true); vozMicrofone.setText("🎙  Falar pedido"); }
    }

    private void processarRespostaVoz(String respostaOriginal) {
        if (!"entrega_voz".equals(telaAtual) || respostaOriginal == null) return;
        liberarReconhecedorVoz();
        restaurarMicrofoneVoz();
        String resposta = normalizarNomeProduto(respostaOriginal).trim();
        if (vozEstado != null) vozEstado.setText("Reconhecido: “" + respostaOriginal.trim() + "”");
        if (etapaVoz.equals("cliente")) {
            if (respostaOriginal.trim().isEmpty()) {
                falar("Não ouvi. Diga o cliente.", null);
                return;
            }
            clienteVoz = nomeClienteMaiusculo(respostaOriginal);
            guardarRascunhoVoz();
            atualizarResumoVoz();
            perguntarVoz("confirmar_cliente", "Cliente " + clienteVoz + ". Confirma?");
        } else if (etapaVoz.equals("confirmar_cliente")) {
            if (respostaComecaSim(resposta)) perguntarDataVoz();
            else perguntarVoz("cliente", "Qual o cliente?");
        } else if (etapaVoz.equals("confirmar_data")) {
            if (respostaComecaSim(resposta)) perguntarProdutoVoz();
            else escolherDataVoz();
        } else if (etapaVoz.equals("produto")) {
            processarItemVoz(respostaOriginal);
        } else if (etapaVoz.equals("confirmar_novo_produto")) {
            if (respostaComecaSim(resposta)) {
                if (itemNovoPendente == null) { perguntarProdutoVoz(); return; }
                if (itemNovoPendente.unidade == null) {
                    perguntarVoz("unidade_novo_produto", "Qual a unidade? Peso, unidade, caixa, maço ou saco.");
                } else adicionarItemNovoVoz(itemNovoPendente);
            } else if (respostaComecaNao(resposta)) {
                perguntarVoz("corrigir_nome_produto", "Diga o nome correto do produto da lista do Monteiro.");
            } else falar("Diga sim se é novo, ou não para corrigir o nome.", null);
        } else if (etapaVoz.equals("corrigir_nome_produto")) {
            String nomeCorreto = produtoCanonico(respostaOriginal);
            if (nomeCorreto == null) {
                if (itemNovoPendente == null) { perguntarProdutoVoz(); return; }
                itemNovoPendente = copiarItemInterpretado(respostaOriginal.trim(), itemNovoPendente);
                guardarRascunhoVoz();
                perguntarVoz("confirmar_novo_produto", "Ainda não encontrei esse nome. É um produto novo?");
            } else if (itemNovoPendente == null) perguntarProdutoVoz();
            else {
                String unidadeCorreta = itemNovoPendente.unidade == null ? obterUnidadeProduto(nomeCorreto) : itemNovoPendente.unidade;
                adicionarItemVoz(new ItemInterpretado(nomeCorreto, itemNovoPendente.medida, unidadeCorreta));
            }
        } else if (etapaVoz.equals("unidade_novo_produto")) {
            String unidadeNova = normalizarUnidade(respostaOriginal);
            if (unidadeNova == null) perguntarVoz("unidade_novo_produto", "Não reconheci. Diga peso, unidade, caixa, maço ou saco.");
            else if (itemNovoPendente == null) perguntarProdutoVoz();
            else adicionarItemNovoVoz(new ItemInterpretado(itemNovoPendente.produto, itemNovoPendente.medida, unidadeNova, true));
        } else if (etapaVoz.equals("proximo_item")) {
            if (respostaComecaNao(resposta) || resposta.contains("ACABOU") || resposta.contains("PRONTO")) {
                confirmarProdutosVoz();
            } else if (resposta.equals("SIM") || resposta.equals("PODE") || resposta.equals("PODE SER")) {
                perguntarProdutoVoz();
            } else {
                processarItemVoz(respostaOriginal);
            }
        } else if (etapaVoz.equals("confirmar_produtos")) {
            if (respostaComecaSim(resposta)) perguntarEnvioVoz();
            else if (respostaComecaNao(resposta)) perguntarProdutoVoz();
            else falar("Diga sim ou não.", null);
        } else if (etapaVoz.equals("enviar")) {
            if (respostaComecaSim(resposta)) enviarPedidoVoz();
            else if (respostaComecaNao(resposta)) perguntarMesmoClienteVoz();
            else falar("Diga sim ou não.", null);
        } else if (etapaVoz.equals("mesmo_cliente")) {
            if (respostaComecaSim(resposta)) {
                itensVoz.clear(); atualizarListaItensVoz(); guardarRascunhoVoz();
                perguntarProdutoVoz();
            } else if (respostaComecaNao(resposta)) {
                itensVoz.clear(); clienteVoz = ""; atualizarListaItensVoz(); atualizarResumoVoz(); guardarRascunhoVoz();
                perguntarVoz("cliente", "Qual o cliente?");
            } else falar("Diga sim ou não.", null);
        }
    }

    private boolean respostaComecaSim(String s) { return s.equals("SIM") || s.startsWith("SIM ") || s.equals("PODE") || s.startsWith("PODE "); }
    private boolean respostaComecaNao(String s) { return s.equals("NAO") || s.startsWith("NAO "); }

    private void perguntarDataVoz() {
        atualizarResumoVoz();
        perguntarVoz("confirmar_data", "Data " + dataVoz + ". Confirma?");
    }

    private void escolherDataVoz() {
        Calendar c = Calendar.getInstance();
        try { c.setTime(new SimpleDateFormat("dd/MM/yyyy", new Locale("pt", "BR")).parse(dataVoz)); } catch (Exception ignored) { }
        new DatePickerDialog(this, (view, ano, mes, dia) -> {
            Calendar escolhida = Calendar.getInstance(); escolhida.set(ano, mes, dia);
            dataVoz = new SimpleDateFormat("dd/MM/yyyy", new Locale("pt", "BR")).format(escolhida.getTime());
            guardarRascunhoVoz();
            atualizarResumoVoz(); perguntarDataVoz();
        }, c.get(Calendar.YEAR), c.get(Calendar.MONTH), c.get(Calendar.DAY_OF_MONTH)).show();
    }

    private void perguntarProdutoVoz() {
        perguntarVoz("produto", "Diga o produto e a quantidade.");
    }

    private void processarItemVoz(String respostaOriginal) {
        List<ItemInterpretado> reconhecidos = interpretarItensVoz(respostaOriginal);
        if (reconhecidos.size() != 1) {
            ItemInterpretado desconhecido = reconhecidos.isEmpty() ? interpretarNovoItemFalado(respostaOriginal) : null;
            if (desconhecido != null && produtoCanonico(desconhecido.produto) == null) {
                itemNovoPendente = desconhecido;
                guardarRascunhoVoz();
                perguntarVoz("confirmar_novo_produto", "Não encontrei " + desconhecido.produto + " na lista do Monteiro. É um produto novo?");
                return;
            }
            vozEstado.setText(reconhecidos.isEmpty()
                ? "Não reconheci o item. Diga produto e quantidade."
                : "Fale um produto por áudio; os demais serão pedidos em seguida.");
            falar(reconhecidos.isEmpty() ? "Não reconheci. Tente novamente." : "Um produto por vez, por favor.", null);
            return;
        }
        adicionarItemVoz(reconhecidos.get(0));
    }

    private void adicionarItemNovoVoz(ItemInterpretado item) {
        adicionarItemVoz(new ItemInterpretado(item.produto, item.medida, item.unidade, true));
        itemNovoPendente = null;
    }

    private void adicionarItemVoz(ItemInterpretado item) {
        itemNovoPendente = null;
        itensVoz.add(item);
        guardarRascunhoVoz();
        atualizarListaItensVoz();
        atualizarResumoVoz();
        perguntarVoz("proximo_item", "Próximo item?");
    }

    private void confirmarProdutosVoz() {
        if (itensVoz.isEmpty()) { perguntarProdutoVoz(); return; }
        StringBuilder resumo = new StringBuilder("Revise: ");
        for (int i = 0; i < itensVoz.size(); i++) {
            ItemInterpretado item = itensVoz.get(i);
            if (i > 0) resumo.append("; ");
            resumo.append(item.produto).append(" ").append(formatarNumero(item.medida)).append(" ").append(unidadeFalavel(item.unidade));
            if (item.novo) resumo.append(" (novo)");
        }
        resumo.append(". Confirma?");
        perguntarVoz("confirmar_produtos", resumo.toString());
    }

    private String unidadeFalavel(String unidade) {
        if ("KG".equals(unidade)) return "quilos";
        if ("UN".equals(unidade)) return "unidades";
        if ("CX".equals(unidade)) return "caixas";
        if ("MC".equals(unidade)) return "maços";
        if ("SC".equals(unidade)) return "sacos";
        return unidade;
    }

    private void perguntarEnvioVoz() {
        perguntarVoz("enviar", "Enviar nota para " + clienteVoz + "?");
    }

    private void perguntarMesmoClienteVoz() {
        perguntarVoz("mesmo_cliente", "Outro pedido para " + clienteVoz + "?");
    }

    private void atualizarResumoVoz() {
        if (vozClienteData != null) vozClienteData.setText("Cliente: " + (clienteVoz.isEmpty() ? "a confirmar" : nomeClienteMaiusculo(clienteVoz)) + "\nData da nota: " + dataVoz);
    }

    private void atualizarListaItensVoz() {
        if (vozLista == null) return;
        if (vozSecaoProdutos != null) vozSecaoProdutos.setText("Produtos (" + itensVoz.size() + ")");
        vozLista.removeAllViews();
        if (itensVoz.isEmpty()) { vozLista.addView(texto("Nenhum produto adicionado ainda.", 15, false)); return; }
        for (int i = 0; i < itensVoz.size(); i++) {
            final int indice = i;
            ItemInterpretado item = itensVoz.get(i);
            LinearLayout linha = new LinearLayout(this); linha.setGravity(Gravity.CENTER_VERTICAL);
            linha.setPadding(dp(12), dp(8), dp(8), dp(8));
            linha.setBackground(fundoComBorda(Color.WHITE, Color.rgb(216, 227, 220), 8));
            LinearLayout.LayoutParams linhaParams = new LinearLayout.LayoutParams(-1, -2); linhaParams.setMargins(0, dp(4), 0, dp(4));
            TextView descricao = texto(item.produto + "\n" + formatarNumero(item.medida) + " " + item.unidade, 16, true);
            LinearLayout detalhes = coluna();
            if (item.novo) detalhes.addView(rotuloNovoProduto());
            detalhes.addView(descricao);
            linha.addView(detalhes, new LinearLayout.LayoutParams(0, -2, 1));
            Button editar = botao("Editar", Color.rgb(37, 99, 235));
            editar.setOnClickListener(v -> editarItemVoz(indice));
            LinearLayout.LayoutParams editarParams = new LinearLayout.LayoutParams(dp(72), dp(42));
            editarParams.setMargins(dp(4), 0, dp(4), 0);
            linha.addView(editar, editarParams);
            Button remover = botao("Remover", Color.rgb(185, 28, 28));
            remover.setOnClickListener(v -> { itensVoz.remove(indice); guardarRascunhoVoz(); atualizarListaItensVoz(); });
            linha.addView(remover, new LinearLayout.LayoutParams(dp(82), dp(42)));
            vozLista.addView(linha, linhaParams);
        }
    }

    private void editarItemVoz(int indice) {
        if (indice < 0 || indice >= itensVoz.size()) return;
        ItemInterpretado atual = itensVoz.get(indice);
        LinearLayout campos = coluna();
        campos.setPadding(dp(20), dp(4), dp(20), 0);
        EditText nome = campo("Produto", InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_CAP_SENTENCES);
        nome.setText(atual.produto);
        EditText quantidade = campo("Quantidade", InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_FLAG_DECIMAL | InputType.TYPE_NUMBER_FLAG_SIGNED);
        quantidade.setText(formatarNumero(atual.medida));
        EditText unidade = campo("Unidade (KG, UN, CX, MC ou SC)", InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_CAP_CHARACTERS);
        unidade.setText(atual.unidade);
        campos.addView(nome);
        campos.addView(quantidade);
        campos.addView(unidade);
        AlertDialog dialog = new AlertDialog.Builder(this).setTitle("Corrigir produto")
            .setView(campos)
            .setNegativeButton("Cancelar", null)
            .setPositiveButton("Salvar", null)
            .create();
        dialog.setOnShowListener(ignored -> dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(view -> {
                String produto = nome.getText().toString().trim();
                Double medida = numero(quantidade.getText().toString());
                String unidadeCorrigida = normalizarUnidade(unidade.getText().toString());
                if (produto.isEmpty() || medida == null || medida <= 0 || unidadeCorrigida == null) {
                    aviso("Informe produto, quantidade maior que zero e unidade válida.");
                    return;
                }
                String canonico = produtoCanonico(produto);
                boolean novo = atual.novo && canonico == null;
                itensVoz.set(indice, new ItemInterpretado(canonico == null ? produto.toUpperCase(new Locale("pt", "BR")) : canonico, medida, unidadeCorrigida, novo));
                guardarRascunhoVoz();
                atualizarListaItensVoz();
                atualizarResumoVoz();
                dialog.dismiss();
            }));
        dialog.show();
    }

    private ItemInterpretado interpretarNovoItemFalado(String fraseOriginal) {
        String frase = limparLinhaPedido(normalizarNumerosFalados(fraseOriginal));
        Matcher m = Pattern.compile("^(.+?)\\s+([0-9]+(?:[\\.,][0-9]+)?)\\s*([A-Za-zÀ-ÿÇçÃãÕõÉéÍíÓóÚúÜü]+)?$").matcher(frase);
        String nome;
        String quantidade;
        String unidadeTexto = null;
        if (m.find()) {
            nome = m.group(1); quantidade = m.group(2); unidadeTexto = m.group(3);
        } else {
            m = Pattern.compile("^([0-9]+(?:[\\.,][0-9]+)?)\\s+([A-Za-zÀ-ÿÇçÃãÕõÉéÍíÓóÚúÜü]+)\\s+(?:de\\s+)?(.+)$").matcher(frase);
            if (m.find()) {
                nome = m.group(3); quantidade = m.group(1); unidadeTexto = m.group(2);
            } else {
                m = Pattern.compile("^([0-9]+(?:[\\.,][0-9]+)?)\\s+(?:de\\s+)?(.+)$").matcher(frase);
                if (!m.find()) return null;
                nome = m.group(2); quantidade = m.group(1);
            }
        }
        nome = nome.replaceAll("^[,;:.\\-–—]+|[,;:.\\-–—]+$", "").replaceAll("\\s+", " ").trim();
        Double medida = numero(quantidade);
        String unidadeNova = unidadeTexto == null ? null : normalizarUnidade(unidadeTexto);
        if (nome.isEmpty() || medida == null || medida <= 0 || (unidadeTexto != null && unidadeNova == null)) return null;
        String nomeExibicao = nome.toUpperCase(new Locale("pt", "BR"));
        if (deveIgnorarLinhaPedido(nomeExibicao) || produtoCanonico(nomeExibicao) != null) return null;
        return new ItemInterpretado(nomeExibicao, medida, unidadeNova, true);
    }

    private ItemInterpretado copiarItemInterpretado(String nome, ItemInterpretado base) {
        return base == null ? null : new ItemInterpretado(nome, base.medida, base.unidade, true);
    }

    private TextView rotuloNovoProduto() {
        TextView tag = texto("NOVO", 11, true);
        tag.setTextColor(Color.rgb(146, 64, 14));
        tag.setPadding(dp(8), dp(2), dp(8), dp(2));
        tag.setBackground(fundoArredondado(Color.rgb(255, 237, 213), 6));
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-2, -2);
        params.setMargins(0, 0, 0, dp(2));
        tag.setLayoutParams(params);
        return tag;
    }

    private String normalizarNumerosFalados(String frase) {
        String n = normalizarNomeProduto(frase).toLowerCase(new Locale("pt", "BR"));
        Map<String, Integer> unidades = new HashMap<>();
        String[] nums = {"zero","um","uma","dois","duas","tres","quatro","cinco","seis","sete","oito","nove","dez","onze","doze","treze","catorze","quatorze","quinze","dezesseis","dezessete","dezoito","dezenove"};
        int[] vals = {0,1,1,2,2,3,4,5,6,7,8,9,10,11,12,13,14,14,15,16,17,18,19};
        for (int i = 0; i < nums.length; i++) unidades.put(nums[i], vals[i]);
        String[] dezenas = {"vinte","trinta","quarenta","cinquenta","sessenta","setenta","oitenta","noventa"};
        for (int i = 0; i < dezenas.length; i++) unidades.put(dezenas[i], (i + 2) * 10);
        String[] centenas = {"cem","cento","duzentos","trezentos","quatrocentos","quinhentos","seiscentos","setecentos","oitocentos","novecentos"};
        int[] cvals = {100,100,200,300,400,500,600,700,800,900};
        for (int i = 0; i < centenas.length; i++) unidades.put(centenas[i], cvals[i]);
        String[] t = n.split("\\s+");
        StringBuilder out = new StringBuilder();
        for (int i = 0; i < t.length;) {
            Integer base = unidades.get(t[i]);
            if (base == null) { if (out.length() > 0) out.append(' '); out.append(t[i++]); continue; }
            int value = base; int j = i + 1;
            if (j < t.length && (t[j].equals("e") || t[j].equals("meio"))) j++;
            if (j < t.length && unidades.containsKey(t[j]) && unidades.get(t[j]) < 10 && base >= 20 && base < 100) { value += unidades.get(t[j]); j++; }
            if (j < t.length && t[j].equals("mil")) { value *= 1000; j++; }
            if (out.length() > 0) out.append(' '); out.append(value); i = j;
        }
        return out.toString().replaceAll(
            "(?i)\\b(\\d+(?:[\\.,]\\d+)?)\\s*(?:kg|kgs|quilo|quilos)\\s+(?:virgula|ponto)\\s*(\\d+)\\s*(?:g|gr|grama|gramas)\\b",
            "$1,$2 KG");
    }

    private void enviarPedidoVoz() {
        prepararNotaVozParaEnvio();
    }

    private void prepararNotaVozParaEnvio() {
        liberarReconhecedorVoz();
        envioOrigemVoz = true;
        etapaVoz = "enviando";
        if (vozMicrofone != null) vozMicrofone.setEnabled(false);
        if (vozSim != null) vozSim.setEnabled(false);
        if (vozNao != null) vozNao.setEnabled(false);
        vozEstado.setText("Preparando a nota no sistema...");
        falar("Enviando nota.", () -> {
            if (!"entrega_voz".equals(telaAtual)) return;
            liberarReconhecedorVoz();
            if (falaVoz != null) { falaVoz.shutdown(); falaVoz = null; }
            falaPronta = false;
            temaEscuroAtivo = true;
            setContentView(criarTela());
            telaAtual = "pedido";
            preencherDataAtual();
            int index = Arrays.asList(CLIENTES_PADRAO).indexOf("OUTRO");
            cliente.setSelection(index < 0 ? 0 : index);
            clienteOutro.setText(clienteVoz.trim().toUpperCase(new Locale("pt", "BR")));
            data.setText(dataVoz);
            itens.clear();
            for (ItemInterpretado item : itensVoz) {
                Double preco = obterPrecoSalvo(item.produto);
                itens.add(new ItemPedido(item.produto, item.medida, item.unidade, preco == null ? 0 : preco, preco != null, item.novo));
            }
            atualizarLista();
            ativarAutosaveRascunho();
            salvarRascunhoNota();
            limparRascunhoVoz();
            prepararEnvioNota(clienteVoz);
        });
    }

    private void encerrarEntregaVoz(boolean voltarMenu) {
        escutaVozAtiva = false;
        tentativaEscutaVoz++;
        liberarReconhecedorVoz();
        if (falaVoz != null) { falaVoz.stop(); falaVoz.shutdown(); falaVoz = null; }
        falaPronta = false; vozRaiz = null; vozLista = null; vozPergunta = null; vozEstado = null; vozMicrofone = null; vozClienteData = null; vozSecaoProdutos = null; vozSim = null; vozNao = null;
        if (voltarMenu) mostrarMenuEntregas();
    }

    private void liberarReconhecedorVoz() {
        if (reconhecedorVoz != null) { reconhecedorVoz.cancel(); reconhecedorVoz.destroy(); reconhecedorVoz = null; }
    }

    private void abrirTelaPedido() {
        temaEscuroAtivo = true;
        telaAtual = "pedido";
        setContentView(criarTela());
        preencherDataAtual();
        boolean temRascunho = perguntarRestaurarRascunho();
        if (!temRascunho) new Handler(Looper.getMainLooper()).postDelayed(() -> sugerirColagemWhatsAppAoAbrir(), 700);
        sincronizarCatalogoMonteiro((disponivel, atualizado) -> {
            if (disponivel && "pedido".equals(telaAtual) && statusEnvioView != null && atualizado)
                statusEnvioView.setText("Lista de produtos do Monteiro atualizada.");
        });
    }

    private boolean perguntarRestaurarRascunho() {
        String salvo = getSharedPreferences("rascunhos_notas", MODE_PRIVATE).getString("atual", "");
        JSONObject rascunho;
        try { rascunho = salvo.isEmpty() ? null : new JSONObject(salvo); }
        catch (Exception e) { rascunho = null; }
        if (rascunho == null) {
            ativarAutosaveRascunho();
            return false;
        }
        JSONArray lista = rascunho.optJSONArray("items");
        String nomeCliente = nomeClienteMaiusculo(rascunho.optString("client_other", ""));
        if (nomeCliente.isEmpty()) nomeCliente = rascunho.optString("client", "");
        String resumo = "Cliente: " + (nomeCliente.isEmpty() ? "a selecionar" : nomeCliente)
            + "\n" + (lista == null ? 0 : lista.length()) + " produto(s) já lançado(s).";
        final JSONObject salvoFinal = rascunho;
        new AlertDialog.Builder(this).setTitle("Rascunho recuperado")
            .setMessage(resumo + "\n\nDeseja continuar de onde parou?")
            .setPositiveButton("Continuar", (d, w) -> {
                aplicarRascunhoNota(salvoFinal);
                ativarAutosaveRascunho();
            })
            .setNegativeButton("Descartar", (d, w) -> {
                limparRascunhoNota();
                ativarAutosaveRascunho();
            })
            .setOnCancelListener(d -> ativarAutosaveRascunho())
            .show();
        return true;
    }

    private void aplicarRascunhoNota(JSONObject salvo) {
        suspenderRascunho = true;
        pedidoId = salvo.optString("external_id", UUID.randomUUID().toString());
        String clienteSalvo = salvo.optString("client", "");
        int clientePos = Arrays.asList(CLIENTES_PADRAO).indexOf(clienteSalvo);
        if (clientePos < 0) clientePos = Arrays.asList(CLIENTES_PADRAO).indexOf("OUTRO");
        cliente.setSelection(Math.max(clientePos, 0));
        clienteOutro.setText(nomeClienteMaiusculo(salvo.optString("client_other", "")));
        clienteOutro.setVisibility("OUTRO".equals(CLIENTES_PADRAO[Math.max(clientePos, 0)]) ? View.VISIBLE : View.GONE);
        data.setText(salvo.optString("date", data.getText().toString()));
        int produtoPos = produtos.indexOf(salvo.optString("product", ""));
        if (produtoPos >= 0) produto.setSelection(produtoPos);
        peso.setText(salvo.optString("weight", ""));
        valor.setText(salvo.optString("value", ""));
        String unidadeSalva = salvo.optString("unit", "");
        for (int i = 0; i < unidade.getCount(); i++)
            if (unidadeSalva.equals(unidade.getItemAtPosition(i).toString())) unidade.setSelection(i);
        itens.clear();
        JSONArray itensSalvos = salvo.optJSONArray("items");
        if (itensSalvos != null) for (int i = 0; i < itensSalvos.length(); i++) {
            JSONObject item = itensSalvos.optJSONObject(i);
            if (item == null) continue;
            boolean temPreco = !item.isNull("unit_price");
            itens.add(new ItemPedido(item.optString("product"), item.optDouble("weight"), item.optString("unit"),
                temPreco ? item.optDouble("unit_price") : 0, temPreco, item.optBoolean("is_new", false)));
        }
        atualizarLista();
        definirStatusEnvio("Rascunho recuperado. Ainda não enviado.", Color.rgb(180, 83, 9));
        suspenderRascunho = false;
    }

    private void ativarAutosaveRascunho() {
        if (!listenersRascunhoAtivos) {
            observarCampoRascunho(clienteOutro);
            observarCampoRascunho(data);
            observarCampoRascunho(peso);
            observarCampoRascunho(valor);
            listenersRascunhoAtivos = true;
        }
        rascunhoPronto = true;
        agendarSalvarRascunho();
    }

    private void observarCampoRascunho(EditText campo) {
        campo.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) { }
            @Override public void onTextChanged(CharSequence s, int start, int before, int count) { agendarSalvarRascunho(); }
            @Override public void afterTextChanged(Editable s) { }
        });
    }

    private void agendarSalvarRascunho() {
        if (!rascunhoPronto || suspenderRascunho || !"pedido".equals(telaAtual)) return;
        if (salvarRascunhoAgendado != null) rascunhoHandler.removeCallbacks(salvarRascunhoAgendado);
        salvarRascunhoAgendado = this::salvarRascunhoNota;
        rascunhoHandler.postDelayed(salvarRascunhoAgendado, 350);
    }

    private synchronized void salvarRascunhoNota() {
        if (!rascunhoPronto || suspenderRascunho || !"pedido".equals(telaAtual)
            || cliente == null || data == null || produto == null || peso == null || valor == null || unidade == null) return;
        try {
            JSONObject rascunho = new JSONObject();
            String clienteSelecionado = cliente.getSelectedItem() == null ? "" : cliente.getSelectedItem().toString();
            String clienteLivre = clienteOutro.getText().toString().trim();
            rascunho.put("external_id", pedidoId);
            rascunho.put("client", nomeClienteMaiusculo(clienteSelecionado));
            rascunho.put("client_other", nomeClienteMaiusculo(clienteLivre));
            rascunho.put("date", data.getText().toString());
            rascunho.put("product", produto.getSelectedItem() == null ? "" : produto.getSelectedItem().toString());
            rascunho.put("weight", peso.getText().toString());
            rascunho.put("value", valor.getText().toString());
            rascunho.put("unit", unidade.getSelectedItem() == null ? "KG" : unidade.getSelectedItem().toString());
            JSONArray lista = new JSONArray();
            for (ItemPedido item : itens) {
                JSONObject salvo = new JSONObject();
                salvo.put("product", item.produto); salvo.put("weight", item.peso); salvo.put("unit", item.unidade);
                salvo.put("unit_price", item.valorInformado ? item.valor : JSONObject.NULL);
                salvo.put("is_new", item.novo); lista.put(salvo);
            }
            rascunho.put("items", lista);
            boolean iniciado = !clienteLivre.isEmpty() || clientePosicionado(clienteSelecionado) || !itens.isEmpty()
                || !peso.getText().toString().trim().isEmpty() || !valor.getText().toString().trim().isEmpty();
            SharedPreferences.Editor editor = getSharedPreferences("rascunhos_notas", MODE_PRIVATE).edit();
            if (iniciado) editor.putString("atual", rascunho.toString()); else editor.remove("atual");
            editor.commit();
        } catch (Exception ignored) { }
    }

    private boolean clientePosicionado(String selecionado) {
        return !selecionado.isEmpty() && !"PALADAR DISTRITO".equals(selecionado);
    }

    private void limparRascunhoNota() {
        if (salvarRascunhoAgendado != null) rascunhoHandler.removeCallbacks(salvarRascunhoAgendado);
        salvarRascunhoAgendado = null;
        getSharedPreferences("rascunhos_notas", MODE_PRIVATE).edit().remove("atual").commit();
    }

    private void definirStatusEnvio(String texto, int cor) {
        if (statusEnvioView == null) return;
        statusEnvioView.setText(texto);
        statusEnvioView.setTextColor(cor);
    }

    private void abrirPlaceholderModulo(String titulo, String mensagem) {
        temaEscuroAtivo = true;
        telaAtual = "placeholder";
        ScrollView scroll = new ScrollView(this);
        scroll.setBackgroundColor(COR_FUNDO_ESCURO);
        LinearLayout raiz = coluna();
        raiz.setBackgroundColor(COR_FUNDO_ESCURO);
        raiz.setPadding(dp(20), dp(22), dp(20), dp(30));
        scroll.addView(raiz);
        adicionarCabecalhoModulo(raiz, titulo, mensagem);
        Button voltar = botao("Voltar para Home", Color.rgb(37, 99, 235));
        voltar.setOnClickListener(v -> mostrarHomeModulos());
        raiz.addView(voltar);
        setContentView(scroll);
    }

    private void adicionarCabecalhoModulo(LinearLayout raiz, String titulo, String subtitulo) {
        LinearLayout topo = new LinearLayout(this);
        topo.setOrientation(LinearLayout.HORIZONTAL);
        topo.setGravity(Gravity.CENTER_VERTICAL);
        Button voltar = new Button(this);
        voltar.setText("‹");
        voltar.setTextSize(28);
        voltar.setAllCaps(false);
        voltar.setTextColor(Color.rgb(20, 83, 45));
        voltar.setBackground(fundoComBorda(Color.WHITE, Color.rgb(216, 227, 220), 12));
        voltar.setOnClickListener(v -> mostrarHomeModulos());
        topo.addView(voltar, new LinearLayout.LayoutParams(dp(48), dp(46)));
        LinearLayout textoTopo = coluna();
        textoTopo.setPadding(dp(12), 0, 0, 0);
        TextView t = texto(titulo, 23, true);
        t.setTextColor(Color.rgb(20, 83, 45));
        t.setMaxLines(1);
        t.setEllipsize(android.text.TextUtils.TruncateAt.END);
        TextView s = texto(subtitulo, 12, false);
        s.setMaxLines(2);
        textoTopo.addView(t);
        textoTopo.addView(s);
        topo.addView(textoTopo, new LinearLayout.LayoutParams(0, -2, 1));
        LinearLayout.LayoutParams topoParams = new LinearLayout.LayoutParams(-1, -2);
        topoParams.setMargins(0, 0, 0, dp(14));
        raiz.addView(topo, topoParams);
    }

    private void adicionarBannerModulo(LinearLayout raiz, String etiqueta, String titulo, String apoio, int cor) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(16), dp(13), dp(16), dp(13));
        card.setBackground(fundoCardModulo(cor));
        TextView tag = texto(etiqueta, 10, true);
        tag.setTextColor(cor);
        TextView chamada = texto(titulo, 17, true);
        chamada.setTextColor(Color.rgb(31, 41, 55));
        chamada.setPadding(0, dp(4), 0, dp(3));
        TextView detalhe = texto(apoio, 12, false);
        detalhe.setTextColor(Color.rgb(75, 85, 99));
        detalhe.setMaxLines(3);
        card.addView(tag);
        card.addView(chamada);
        card.addView(detalhe);
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-1, -2);
        params.setMargins(0, 0, 0, dp(12));
        raiz.addView(card, params);
    }

    private void adicionarEtapasPedido(LinearLayout raiz) {
        LinearLayout etapas = new LinearLayout(this);
        etapas.setOrientation(LinearLayout.HORIZONTAL);
        etapas.setGravity(Gravity.CENTER_VERTICAL);
        String[] nomes = {"1  Cliente", "2  Produtos", "3  Revisar"};
        for (int i = 0; i < nomes.length; i++) {
            TextView etapa = texto(nomes[i], 11, true);
            etapa.setSingleLine(true);
            etapa.setGravity(Gravity.CENTER);
            etapa.setTextColor(i == 0 ? Color.WHITE : Color.rgb(75, 85, 99));
            etapa.setPadding(dp(5), dp(9), dp(5), dp(9));
            etapa.setBackground(fundoComBorda(i == 0 ? Color.rgb(21, 101, 52) : Color.WHITE,
                i == 0 ? Color.rgb(21, 101, 52) : Color.rgb(216, 227, 220), 10));
            LinearLayout.LayoutParams etapaParams = new LinearLayout.LayoutParams(0, -2, 1);
            etapaParams.setMargins(i == 0 ? 0 : dp(5), 0, 0, dp(10));
            etapas.addView(etapa, etapaParams);
        }
        raiz.addView(etapas);
    }

    private void abrirModuloProdutos() {
        temaEscuroAtivo = true;
        telaAtual = "produtos_precos";
        ScrollView scroll = new ScrollView(this);
        scroll.setBackgroundColor(COR_FUNDO_ESCURO);
        LinearLayout raiz = coluna();
        raiz.setBackgroundColor(COR_FUNDO_ESCURO);
        raiz.setPadding(dp(18), dp(18), dp(18), dp(28));
        scroll.addView(raiz);
        adicionarCabecalhoModulo(raiz, "Produtos", "Tabela de preços da Menina dos Raios · somente consulta.");

        LinearLayout controles = new LinearLayout(this);
        controles.setOrientation(LinearLayout.HORIZONTAL);
        controles.setGravity(Gravity.CENTER_VERTICAL);
        EditText busca = campo("Buscar produto", InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS);
        controles.addView(busca, new LinearLayout.LayoutParams(0, dp(48), 1));
        Button atualizar = botao("↻ Atualizar", Color.rgb(21, 101, 52));
        atualizar.setTextSize(13);
        atualizar.setLayoutParams(new LinearLayout.LayoutParams(-1, dp(44)));
        LinearLayout.LayoutParams atualizarParams = new LinearLayout.LayoutParams(-2, dp(44));
        atualizarParams.setMargins(dp(8), 0, 0, 0);
        controles.addView(atualizar, atualizarParams);
        raiz.addView(controles);

        TextView status = texto("Carregando preços...", 13, false);
        status.setPadding(0, dp(10), 0, dp(6));
        raiz.addView(status);
        LinearLayout lista = coluna();
        raiz.addView(lista);
        Button voltar = botao("Voltar para Home", Color.rgb(37, 99, 235));
        LinearLayout.LayoutParams voltarParams = new LinearLayout.LayoutParams(-1, dp(44));
        voltarParams.setMargins(0, dp(14), 0, 0);
        raiz.addView(voltar, voltarParams);
        voltar.setOnClickListener(v -> mostrarHomeModulos());
        busca.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            @Override public void onTextChanged(CharSequence s, int start, int before, int count) {
                renderizarPrecosProdutos(lista, status, precosProdutos, s == null ? "" : s.toString());
            }
            @Override public void afterTextChanged(Editable s) {}
        });
        atualizar.setOnClickListener(v -> carregarPrecosProdutos(lista, status, busca));
        setContentView(scroll);
        carregarPrecosProdutos(lista, status, busca);
    }

    private JSONArray precosProdutos = new JSONArray();

    private void carregarPrecosProdutos(LinearLayout lista, TextView status, EditText busca) {
        status.setText("Carregando preços...");
        new Thread(() -> {
            try {
                JSONArray dados = buscarArrayApi("/api/prices");
                runOnUiThread(() -> {
                    precosProdutos = dados;
                    renderizarPrecosProdutos(lista, status, dados, busca.getText().toString());
                });
            } catch (Exception e) {
                runOnUiThread(() -> {
                    lista.removeAllViews();
                    status.setText("Não foi possível carregar os preços. Verifique a conexão e tente atualizar.");
                });
            }
        }).start();
    }

    private void renderizarPrecosProdutos(LinearLayout lista, TextView status, JSONArray dados, String consulta) {
        lista.removeAllViews();
        String filtro = semAcento(consulta == null ? "" : consulta.trim()).toLowerCase(new Locale("pt", "BR"));
        int encontrados = 0;
        for (int i = 0; i < dados.length(); i++) {
            JSONObject item = dados.optJSONObject(i);
            if (item == null) continue;
            String nome = item.optString("label", "Produto").trim();
            if (!semAcento(nome).toLowerCase(new Locale("pt", "BR")).contains(filtro)) continue;
            encontrados++;
            LinearLayout linha = new LinearLayout(this);
            linha.setOrientation(LinearLayout.HORIZONTAL);
            linha.setGravity(Gravity.CENTER_VERTICAL);
            linha.setPadding(dp(14), dp(10), dp(14), dp(10));
            linha.setBackground(fundoComBorda(Color.WHITE, Color.rgb(216, 227, 220), 10));
            LinearLayout.LayoutParams linhaParams = new LinearLayout.LayoutParams(-1, -2);
            linhaParams.setMargins(0, dp(5), 0, dp(5));
            lista.addView(linha, linhaParams);
            TextView produto = texto(nome, 15, true);
            linha.addView(produto, new LinearLayout.LayoutParams(0, -2, 1));
            TextView preco = texto(formatarPrecoProduto(item), 15, true);
            preco.setTextColor(Color.rgb(20, 83, 45));
            preco.setGravity(Gravity.RIGHT | Gravity.CENTER_VERTICAL);
            linha.addView(preco);
        }
        status.setText(encontrados + (encontrados == 1 ? " produto" : " produtos") + " · preços para consulta");
        if (encontrados == 0) lista.addView(texto("Nenhum produto encontrado.", 14, false));
    }

    private String formatarPrecoProduto(JSONObject item) {
        double preco = item.optDouble("price", 0);
        if (item.optBoolean("is_variable", false)) {
            double minimo = item.optDouble("price_min", Double.NaN);
            double maximo = item.optDouble("price_max", Double.NaN);
            if (!Double.isNaN(minimo) && !Double.isNaN(maximo) && minimo > 0 && maximo > 0) {
                return moeda.format(minimo) + " – " + moeda.format(maximo);
            }
            return preco > 0 ? "A partir de " + moeda.format(preco) : "Preço variável";
        }
        return preco > 0 ? moeda.format(preco) : "Preço não informado";
    }

    private JSONArray mobileBoletoClients = new JSONArray();
    private JSONArray mobileBoletoRows = new JSONArray();
    private String mobileBoletoStatusFilter = "pendente";
    private String mobileBoletoClientFilter = "todos";
    private boolean mobileBoletoAlertEnabled = true;
    private int mobileBoletoPage = 0;
    private int mobileBoletoClientPage = 0;
    private static final int MOBILE_BOLETOS_PAGE_SIZE = 20;
    private JSONArray mobileNovoTempoRows = new JSONArray();
    private int mobileNovoTempoPage = 0;
    private String mobileNovoTempoFilter = "pendente";

    private void abrirModuloEstoque(String moduloInicial) {
        temaEscuroAtivo = true;
        telaAtual = "estoque";
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(COR_FUNDO_ESCURO);
        LinearLayout raiz = coluna();
        raiz.setPadding(dp(16), dp(14), dp(16), dp(24));
        scroll.addView(raiz);
        adicionarCabecalhoModulo(raiz, "Estoque", "Consulte saldos e registre entradas no ERP.");
        Spinner modulo = new Spinner(this);
        String[] modulos = {"Menina dos Raios", "Menina da Estrada"};
        modulo.setAdapter(adaptadorSpinner(modulos));
        modulo.setSelection("estrada".equals(moduloInicial) ? 1 : 0);
        raiz.addView(rotuloCampo("EMPRESA"));
        raiz.addView(modulo);
        LinearLayout acoes = new LinearLayout(this);
        acoes.setOrientation(LinearLayout.HORIZONTAL);
        Button adicionarProduto = botao("＋ Produto", Color.rgb(21, 101, 52));
        Button registrarEntrada = botao("＋ Entrada", Color.rgb(21, 128, 61));
        acoes.addView(adicionarProduto, new LinearLayout.LayoutParams(0, dp(48), 1));
        LinearLayout.LayoutParams entradaParams = new LinearLayout.LayoutParams(0, dp(48), 1);
        entradaParams.setMargins(dp(8), 0, 0, 0);
        acoes.addView(registrarEntrada, entradaParams);
        raiz.addView(acoes);
        TextView estado = texto("Carregando saldos...", 13, false);
        estado.setPadding(0, dp(10), 0, dp(4));
        raiz.addView(estado);
        LinearLayout lista = coluna();
        raiz.addView(lista);
        final JSONArray[] produtosAtuais = {new JSONArray()};
        final Runnable[] carregarRef = {null};
        Runnable carregar = () -> {
            String chave = modulo.getSelectedItemPosition() == 1 ? "estrada" : "raios";
            estado.setText("Atualizando estoque...");
            new Thread(() -> {
                try {
                    JSONObject resposta = buscarObjetoApi("/api/stock?module=" + chave);
                    JSONArray produtos = resposta.optJSONArray("products");
                    if (produtos == null) produtos = new JSONArray();
                    JSONArray finalProdutos = produtos;
                    runOnUiThread(() -> {
                        produtosAtuais[0] = finalProdutos;
                        lista.removeAllViews();
                        estado.setText(finalProdutos.length() + " produto(s) neste estoque · atualizado agora");
                        if (finalProdutos.length() == 0) lista.addView(cardLeitura("Nenhum produto cadastrado", "Cadastre um produto para começar a movimentação.", "", "", Color.rgb(240, 249, 244)));
                        for (int i = 0; i < finalProdutos.length(); i++) {
                            JSONObject item = finalProdutos.optJSONObject(i);
                            if (item == null) continue;
                            double saldoValor = item.optDouble("balance", 0);
                            String saldo = formatarNumero(saldoValor) + " " + item.optString("unit", "UN");
                            View cartaoProduto = cardSaldoEstoque(item.optString("name", "Produto"), item.optString("sku", "—"), saldo,
                                item.optInt("sales_count", 0), saldoValor);
                            cartaoProduto.setContentDescription("Adicionar entrada ao estoque para " + item.optString("name", "Produto"));
                            cartaoProduto.setOnClickListener(v -> dialogEntradaProdutoEstoque(chave, item, carregarRef[0]));
                            cartaoProduto.setFocusable(true);
                            lista.addView(cartaoProduto);
                        }
                    });
                } catch (Exception e) {
                    runOnUiThread(() -> {
                        lista.removeAllViews(); estado.setText("Não foi possível consultar o estoque.");
                        lista.addView(cardLeitura("Estoque indisponível", "Confira a conexão e seu acesso ao módulo da empresa.", "", mensagemErroSimples(e), Color.rgb(255, 247, 237)));
                    });
                }
            }).start();
        };
        carregarRef[0] = carregar;
        modulo.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {
            @Override public void onItemSelected(AdapterView<?> parent, View view, int position, long id) { carregar.run(); }
            @Override public void onNothingSelected(AdapterView<?> parent) { }
        });
        adicionarProduto.setOnClickListener(v -> dialogNovoProdutoEstoque(modulo.getSelectedItemPosition() == 1 ? "estrada" : "raios", carregar));
        registrarEntrada.setOnClickListener(v -> dialogEntradaEstoque(modulo.getSelectedItemPosition() == 1 ? "estrada" : "raios", produtosAtuais[0], carregar));
        setContentView(scroll);
    }

    private void dialogNovoProdutoEstoque(String modulo, Runnable aoSalvar) {
        LinearLayout form = coluna(); form.setPadding(dp(18), dp(8), dp(18), dp(4));
        EditText nome = campo("Nome do produto", InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_CAP_SENTENCES);
        EditText sku = campo("Código interno (SKU)", InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_CAP_CHARACTERS);
        EditText unidade = campo("Unidade de controle (ex.: UN, KG, CX)", InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_CAP_CHARACTERS);
        EditText aliases = campo("Nomes usados nas vendas (opcional)", InputType.TYPE_CLASS_TEXT);
        form.addView(rotuloCampo("NOME")); form.addView(nome);
        form.addView(rotuloCampo("SKU")); form.addView(sku);
        form.addView(rotuloCampo("UNIDADE")); form.addView(unidade);
        form.addView(rotuloCampo("ALIASES")); form.addView(aliases);
        ScrollView scroll = new ScrollView(this); scroll.addView(form);
        AlertDialog dialog = new AlertDialog.Builder(this).setTitle("Cadastrar produto no estoque")
            .setView(scroll).setNegativeButton("Cancelar", null).setPositiveButton("Cadastrar", null).create();
        dialog.setOnShowListener(ignored -> dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(view -> {
            String productName = nome.getText().toString().trim();
            String productSku = sku.getText().toString().trim();
            String productUnit = unidade.getText().toString().trim();
            if (productName.isEmpty() || productSku.isEmpty() || productUnit.isEmpty()) { aviso("Preencha nome, SKU e unidade."); return; }
            JSONArray listaAliases = new JSONArray();
            for (String alias : aliases.getText().toString().split(",")) if (!alias.trim().isEmpty()) listaAliases.put(alias.trim());
            JSONObject body = new JSONObject();
            try { body.put("module", modulo); body.put("name", productName); body.put("sku", productSku); body.put("unit", productUnit); body.put("aliases", listaAliases); }
            catch (Exception e) { aviso("Não foi possível preparar o produto."); return; }
            view.setEnabled(false);
            new Thread(() -> {
                try {
                    enviarObjetoApi("/api/stock/products", "POST", body);
                    runOnUiThread(() -> { dialog.dismiss(); aviso("Produto cadastrado no estoque do ERP."); aoSalvar.run(); });
                } catch (Exception e) { runOnUiThread(() -> { view.setEnabled(true); aviso("Não foi possível cadastrar: " + mensagemErroSimples(e)); }); }
            }).start();
        }));
        dialog.show();
    }

    private void dialogEntradaEstoque(String modulo, JSONArray produtos, Runnable aoSalvar) {
        if (produtos == null || produtos.length() == 0) { aviso("Cadastre ou atualize os produtos antes de registrar uma entrada."); return; }
        LinearLayout form = coluna(); form.setPadding(dp(18), dp(6), dp(18), dp(4));
        Spinner produto = new Spinner(this);
        List<String> nomes = new ArrayList<>();
        for (int i = 0; i < produtos.length(); i++) { JSONObject row = produtos.optJSONObject(i); if (row != null) nomes.add(row.optString("name") + " · " + row.optString("unit")); }
        produto.setAdapter(adaptadorSpinner(nomes));
        EditText quantidade = campo("Quantidade recebida", InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_FLAG_DECIMAL);
        quantidade.setKeyListener(DigitsKeyListener.getInstance("0123456789,."));
        EditText referencia = campo("Referência (NF, compra, inventário)", InputType.TYPE_CLASS_TEXT);
        EditText observacao = campo("Observação (opcional)", InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_CAP_SENTENCES);
        form.addView(rotuloCampo("PRODUTO")); form.addView(produto);
        form.addView(rotuloCampo("QUANTIDADE")); form.addView(quantidade);
        form.addView(rotuloCampo("REFERÊNCIA")); form.addView(referencia);
        form.addView(rotuloCampo("OBSERVAÇÃO")); form.addView(observacao);
        ScrollView scroll = new ScrollView(this); scroll.addView(form);
        AlertDialog dialog = new AlertDialog.Builder(this).setTitle("Registrar entrada no estoque")
            .setView(scroll).setNegativeButton("Cancelar", null).setPositiveButton("Registrar", null).create();
        dialog.setOnShowListener(ignored -> dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(view -> {
            JSONObject selected = produtos.optJSONObject(produto.getSelectedItemPosition());
            double qty;
            try { qty = Double.parseDouble(quantidade.getText().toString().replace(',', '.')); }
            catch (Exception e) { qty = 0; }
            if (selected == null || qty <= 0 || !Double.isFinite(qty)) { aviso("Escolha um produto e informe uma quantidade válida."); return; }
            JSONObject body = new JSONObject();
            String dataHoje = new SimpleDateFormat("yyyy-MM-dd", Locale.US).format(Calendar.getInstance().getTime());
            try { body.put("module", modulo); body.put("product_id", selected.optString("id")); body.put("movement_type", "entry"); body.put("quantity", qty); body.put("unit", selected.optString("unit", "UN")); body.put("movement_date", dataHoje); body.put("reference", referencia.getText().toString().trim()); body.put("notes", observacao.getText().toString().trim()); }
            catch (Exception e) { aviso("Não foi possível preparar a entrada."); return; }
            view.setEnabled(false);
            new Thread(() -> {
                try {
                    enviarObjetoApi("/api/stock/movements", "POST", body);
                    runOnUiThread(() -> { dialog.dismiss(); aviso("Entrada registrada no estoque do ERP."); aoSalvar.run(); });
                } catch (Exception e) { runOnUiThread(() -> { view.setEnabled(true); aviso("Entrada não registrada: " + mensagemErroSimples(e)); }); }
            }).start();
        }));
        dialog.show();
    }

    private void dialogEntradaProdutoEstoque(String modulo, JSONObject produto, Runnable aoSalvar) {
        if (produto == null) return;
        String unidadeInformada = produto.optString("unit", "UN").trim().toUpperCase(Locale.ROOT);
        final String unidadeControle = unidadeInformada.isEmpty() ? "UN" : unidadeInformada;
        String unidadeAlternativa = "KG".equals(unidadeControle) ? "UN" : "KG";
        LinearLayout form = coluna(); form.setPadding(dp(18), dp(8), dp(18), dp(4));
        TextView explicacao = texto("Saldo deste produto é controlado em " + unidadeControle + ". Selecione a mesma unidade para manter a contagem correta.", 13, false);
        explicacao.setPadding(0, 0, 0, dp(8));
        Spinner unidade = new Spinner(this);
        unidade.setAdapter(adaptadorSpinner(Arrays.asList(unidadeControle, unidadeAlternativa)));
        unidade.setSelection(0);
        EditText quantidade = campo("Quantidade recebida", InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_FLAG_DECIMAL);
        quantidade.setKeyListener(DigitsKeyListener.getInstance("0123456789,."));
        form.addView(texto(produto.optString("name", "Produto"), 19, true));
        form.addView(explicacao);
        form.addView(rotuloCampo("UNIDADE DA ENTRADA")); form.addView(unidade);
        form.addView(rotuloCampo("QUANTIDADE")); form.addView(quantidade);
        AlertDialog dialog = new AlertDialog.Builder(this).setTitle("Adicionar ao estoque")
            .setView(form).setNegativeButton("Cancelar", null).setPositiveButton("Adicionar", null).create();
        dialog.setOnShowListener(ignored -> dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(view -> {
            String unidadeEscolhida = String.valueOf(unidade.getSelectedItem()).trim().toUpperCase(Locale.ROOT);
            if (!unidadeControle.equals(unidadeEscolhida)) {
                aviso("Este SKU controla saldo em " + unidadeControle + ". Selecione essa unidade; o sistema não converte KG e unidades automaticamente.");
                return;
            }
            double qty;
            try { qty = Double.parseDouble(quantidade.getText().toString().replace(',', '.')); }
            catch (Exception e) { qty = 0; }
            if (qty <= 0 || !Double.isFinite(qty)) { aviso("Informe uma quantidade válida maior que zero."); return; }
            JSONObject body = new JSONObject();
            try {
                body.put("module", modulo); body.put("product_id", produto.optString("id"));
                body.put("movement_type", "entry"); body.put("quantity", qty); body.put("unit", unidadeEscolhida);
                body.put("movement_date", new SimpleDateFormat("yyyy-MM-dd", Locale.US).format(Calendar.getInstance().getTime()));
                body.put("reference", "Entrada manual pelo APK");
            } catch (Exception e) { aviso("Não foi possível preparar a entrada."); return; }
            view.setEnabled(false);
            new Thread(() -> {
                try {
                    enviarObjetoApi("/api/stock/movements", "POST", body);
                    runOnUiThread(() -> { dialog.dismiss(); aviso("Entrada adicionada ao estoque."); aoSalvar.run(); });
                } catch (Exception e) { runOnUiThread(() -> { view.setEnabled(true); aviso("Entrada não registrada: " + mensagemErroSimples(e)); }); }
            }).start();
        }));
        dialog.show();
    }

    private void abrirModuloBoletos() {
        if (!"admin".equalsIgnoreCase(authPrefs().getString("role", "").trim())) {
            aviso("Apenas contas admin podem acessar os boletos.");
            return;
        }
        temaEscuroAtivo = true;
        telaAtual = "boletos_admin";
        LinearLayout tela = coluna();
        tela.setBackgroundColor(COR_FUNDO_ESCURO);
        ScrollView scroll = new ScrollView(this);
        LinearLayout conteudo = coluna();
        conteudo.setPadding(dp(18), dp(12), dp(18), dp(18));
        scroll.addView(conteudo);
        tela.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 1));

        TextView titulo = texto("Boletos", 25, true);
        titulo.setTextColor(Color.rgb(20, 83, 45));
        titulo.setGravity(Gravity.LEFT);
        conteudo.addView(titulo);
        conteudo.addView(texto("Acompanhe vencimentos e clientes selecionados no ERP.", 13, false));
        TextView status = texto("Carregando carteira...", 12, false);
        conteudo.addView(status);
        Button relatorioDevedor = botao("▤  Relatório de débitos", Color.rgb(21, 101, 52));
        conteudo.addView(relatorioDevedor);
        relatorioDevedor.setOnClickListener(v -> abrirSeletorRelatorioDebitos());

        LinearLayout indicadores = new LinearLayout(this);
        indicadores.setOrientation(LinearLayout.HORIZONTAL);
        TextView totalAberto = texto("Em aberto\n—", 13, true);
        TextView totalAtraso = texto("Em atraso\n—", 13, true);
        totalAberto.setPadding(dp(10), dp(10), dp(8), dp(10));
        totalAtraso.setPadding(dp(10), dp(10), dp(8), dp(10));
        totalAberto.setBackground(fundoComBorda(Color.WHITE, Color.rgb(216, 227, 220), 10));
        totalAtraso.setBackground(fundoComBorda(Color.WHITE, Color.rgb(216, 227, 220), 10));
        LinearLayout.LayoutParams indicador1 = new LinearLayout.LayoutParams(0, -2, 1);
        indicador1.setMargins(0, dp(8), dp(4), dp(8));
        LinearLayout.LayoutParams indicador2 = new LinearLayout.LayoutParams(0, -2, 1);
        indicador2.setMargins(dp(4), dp(8), 0, dp(8));
        indicadores.addView(totalAberto, indicador1);
        indicadores.addView(totalAtraso, indicador2);
        conteudo.addView(indicadores);

        LinearLayout abas = coluna();
        LinearLayout primeiraLinhaAbas = new LinearLayout(this);
        LinearLayout segundaLinhaAbas = new LinearLayout(this);
        primeiraLinhaAbas.setOrientation(LinearLayout.HORIZONTAL);
        segundaLinhaAbas.setOrientation(LinearLayout.HORIZONTAL);
        Button pendentes = botaoFiltroBoleto("Pendentes", "pendente");
        Button vencidos = botaoFiltroBoleto("Vencidos", "vencido");
        Button pagos = botaoFiltroBoleto("Pagos", "pago");
        Button alertasNovoTempo = botaoFiltroBoleto("Alertas", "alertas");
        for (Button tab : new Button[]{pendentes, vencidos, pagos, alertasNovoTempo}) {
            tab.setTextSize(12);
            tab.setMinWidth(0);
            tab.setPadding(dp(6), 0, dp(6), 0);
            tab.setMaxLines(2);
        }
        primeiraLinhaAbas.addView(pendentes, new LinearLayout.LayoutParams(0, dp(46), 1));
        primeiraLinhaAbas.addView(vencidos, new LinearLayout.LayoutParams(0, dp(46), 1));
        segundaLinhaAbas.addView(pagos, new LinearLayout.LayoutParams(0, dp(46), 1));
        segundaLinhaAbas.addView(alertasNovoTempo, new LinearLayout.LayoutParams(0, dp(46), 1));
        abas.addView(primeiraLinhaAbas);
        abas.addView(segundaLinhaAbas);
        conteudo.addView(abas);

        EditText busca = campo("Buscar cliente ou NF", InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS);
        conteudo.addView(busca);
        LinearLayout boletos = coluna();
        TextView configurar = texto("☷  Configurar clientes  ›\nEscolher quem acompanhar e notificar", 14, true);
        configurar.setPadding(dp(14), dp(12), dp(12), dp(12));
        configurar.setBackground(fundoComBorda(Color.WHITE, Color.rgb(216, 227, 220), 10));
        LinearLayout.LayoutParams configurarParams = new LinearLayout.LayoutParams(-1, -2);
        configurarParams.setMargins(0, dp(12), 0, dp(6));
        conteudo.addView(configurar, configurarParams);
        configurar.setOnClickListener(v -> abrirConfiguracaoBoletos());
        aplicarFeedbackToque(configurar);
        conteudo.addView(boletos);

        LinearLayout rodape = new LinearLayout(this);
        rodape.setPadding(dp(14), dp(8), dp(14), dp(8));
        rodape.setBackgroundColor(Color.WHITE);
        Button atualizar = botao("Atualizar boletos  ↻", Color.rgb(21, 101, 52));
        rodape.addView(atualizar);
        tela.addView(rodape, new LinearLayout.LayoutParams(-1, -2));
        atualizar.setOnClickListener(v -> {
            if ("alertas".equals(mobileBoletoStatusFilter)) carregarAlertasNovoTempo(status, totalAberto, totalAtraso, boletos, busca);
            else carregarCarteiraBoletos(status, totalAberto, totalAtraso, boletos, busca);
        });
        pendentes.setOnClickListener(v -> {
            mobileBoletoStatusFilter = "pendente";
            mobileBoletoPage = 0;
            atualizarBotoesFiltroBoleto(pendentes, vencidos, pagos);
            estilizarBotaoFiltroBoleto(alertasNovoTempo, false);
            busca.setHint("Buscar cliente ou NF");
            renderizarCarteiraBoletos(status, totalAberto, totalAtraso, boletos, busca.getText().toString());
        });
        vencidos.setOnClickListener(v -> {
            mobileBoletoStatusFilter = "vencido";
            mobileBoletoPage = 0;
            atualizarBotoesFiltroBoleto(pendentes, vencidos, pagos);
            estilizarBotaoFiltroBoleto(alertasNovoTempo, false);
            busca.setHint("Buscar cliente ou NF");
            renderizarCarteiraBoletos(status, totalAberto, totalAtraso, boletos, busca.getText().toString());
        });
        pagos.setOnClickListener(v -> {
            mobileBoletoStatusFilter = "pago";
            mobileBoletoPage = 0;
            atualizarBotoesFiltroBoleto(pendentes, vencidos, pagos);
            estilizarBotaoFiltroBoleto(alertasNovoTempo, false);
            busca.setHint("Buscar cliente ou NF");
            renderizarCarteiraBoletos(status, totalAberto, totalAtraso, boletos, busca.getText().toString());
        });
        busca.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            @Override public void onTextChanged(CharSequence s, int start, int before, int count) {
                mobileBoletoPage = 0;
                if ("alertas".equals(mobileBoletoStatusFilter)) {
                    mobileNovoTempoPage = 0;
                    renderizarAlertasNovoTempo(status, totalAberto, totalAtraso, boletos, s == null ? "" : s.toString());
                } else renderizarCarteiraBoletos(status, totalAberto, totalAtraso, boletos, s == null ? "" : s.toString());
            }
            @Override public void afterTextChanged(Editable s) {}
        });
        alertasNovoTempo.setOnClickListener(v -> {
            mobileBoletoStatusFilter = "alertas";
            mobileNovoTempoPage = 0;
            mobileNovoTempoFilter = "pendente";
            atualizarBotoesFiltroBoleto(pendentes, vencidos, pagos);
            estilizarBotaoFiltroBoleto(alertasNovoTempo, true);
            busca.setHint("Buscar filial ou NF Novo Tempo");
            busca.setText("");
            carregarAlertasNovoTempo(status, totalAberto, totalAtraso, boletos, busca);
        });
        setContentView(tela);
        carregarCarteiraBoletos(status, totalAberto, totalAtraso, boletos, busca);
    }

    private Button botaoFiltroBoleto(String label, String filtro) {
        Button botao = new Button(this);
        botao.setText(label);
        botao.setAllCaps(false);
        botao.setTextSize(12);
        botao.setTypeface(null, 1);
        estilizarBotaoFiltroBoleto(botao, filtro.equals(mobileBoletoStatusFilter));
        return botao;
    }

    private void atualizarBotoesFiltroBoleto(Button pendentes, Button vencidos, Button pagos) {
        estilizarBotaoFiltroBoleto(pendentes, "pendente".equals(mobileBoletoStatusFilter));
        estilizarBotaoFiltroBoleto(vencidos, "vencido".equals(mobileBoletoStatusFilter));
        estilizarBotaoFiltroBoleto(pagos, "pago".equals(mobileBoletoStatusFilter));
    }

    private void estilizarBotaoFiltroBoleto(Button botao, boolean ativo) {
        int verde = Color.rgb(21, 101, 52);
        int fundo = ativo ? verde : Color.rgb(240, 245, 241);
        botao.setTextColor(ativo ? Color.WHITE : Color.rgb(39, 57, 45));
        botao.setBackground(fundoComBorda(fundo, fundo, 9));
    }

    private void carregarCarteiraBoletos(TextView status, TextView totalAberto, TextView totalAtraso, LinearLayout destino, EditText busca) {
        status.setText("Atualizando carteira...");
        new Thread(() -> {
            try {
                JSONObject config = buscarObjetoApi(MOBILE_BOLETOS_CONFIG_URL);
                JSONArray linhas = buscarArrayApi("/api/boletos");
                JSONObject atraso = buscarObjetoApi(MOBILE_BOLETOS_OVERDUE_URL);
                runOnUiThread(() -> {
                    mobileBoletoClients = config.optJSONArray("clients") == null ? new JSONArray() : config.optJSONArray("clients");
                    mobileBoletoRows = linhas;
                    mobileBoletoAlertEnabled = config.optBoolean("alert_enabled", true);
                    atualizarTotaisBoletos(totalAberto, totalAtraso, atraso);
                    status.setText("Boletos dos clientes acompanhados");
                    renderizarCarteiraBoletos(status, totalAberto, totalAtraso, destino, busca.getText().toString());
                });
            } catch (Exception e) {
                runOnUiThread(() -> status.setText("Não foi possível carregar a carteira. Verifique a conexão e tente atualizar."));
            }
        }).start();
    }

    private void carregarAlertasNovoTempo(TextView status, TextView aberto, TextView atraso, LinearLayout destino, EditText busca) {
        status.setText("Carregando cobranças Novo Tempo...");
        new Thread(() -> {
            try {
                JSONArray rows = buscarArrayApi("/api/mobile/new-tempo/collections");
                runOnUiThread(() -> {
                    mobileNovoTempoRows = rows;
                    status.setText("Cobranças de todas as filiais Novo Tempo");
                    renderizarAlertasNovoTempo(status, aberto, atraso, destino, busca.getText().toString());
                });
            } catch (Exception e) {
                runOnUiThread(() -> status.setText("Não foi possível carregar os alertas. Verifique a conexão e tente atualizar."));
            }
        }).start();
    }

    private void renderizarAlertasNovoTempo(TextView status, TextView aberto, TextView atraso, LinearLayout destino, String consulta) {
        destino.removeAllViews();
        int pendentes = 0, aguardando = 0, pagos = 0;
        double valorPendente = 0;
        ArrayList<JSONObject> filtrados = new ArrayList<>();
        String termo = semAcento(consulta == null ? "" : consulta.trim()).toLowerCase(new Locale("pt", "BR"));
        for (int i = 0; i < mobileNovoTempoRows.length(); i++) {
            JSONObject row = mobileNovoTempoRows.optJSONObject(i);
            if (row == null) continue;
            boolean pago = "pago".equalsIgnoreCase(row.optString("status", "pendente"));
            if (pago) pagos++;
            else {
                pendentes++;
                valorPendente += row.optDouble("total", 0);
                if (!row.optBoolean("notifications_due", false)) aguardando++;
            }
            if (pago != "pago".equals(mobileNovoTempoFilter)) continue;
            String alvo = semAcento(row.optString("client", "") + " " + row.optString("nf_number", "")).toLowerCase(new Locale("pt", "BR"));
            if (!termo.isEmpty() && !alvo.contains(termo)) continue;
            filtrados.add(row);
        }
        aberto.setText("Pendentes Novo Tempo\n" + pendentes + " · " + moeda.format(valorPendente));
        atraso.setText("Aguardando 24h\n" + aguardando + " · pagos " + pagos);
        destino.addView(texto("Novo Tempo · cobranças pendentes", 18, true));
        destino.addView(texto("Somente notas entregues geram alertas. O primeiro aviso sai 24h após a entrega; depois às 08h, 12h, 16h e 20h, até a baixa. Notificações somente para admins.", 13, false));
        adicionarEstadoNotificacoesNovoTempo(destino);
        LinearLayout filtros = new LinearLayout(this);
        Button filtroPendentes = botaoFiltroBoleto("Pendentes (" + pendentes + ")", "pendente");
        Button filtroPagos = botaoFiltroBoleto("Pagos (" + pagos + ")", "pago");
        estilizarBotaoFiltroBoleto(filtroPendentes, "pendente".equals(mobileNovoTempoFilter));
        estilizarBotaoFiltroBoleto(filtroPagos, "pago".equals(mobileNovoTempoFilter));
        filtros.addView(filtroPendentes, new LinearLayout.LayoutParams(0, dp(42), 1));
        filtros.addView(filtroPagos, new LinearLayout.LayoutParams(0, dp(42), 1));
        destino.addView(filtros);
        filtroPendentes.setOnClickListener(v -> { mobileNovoTempoFilter = "pendente"; mobileNovoTempoPage = 0; renderizarAlertasNovoTempo(status, aberto, atraso, destino, consulta); });
        filtroPagos.setOnClickListener(v -> { mobileNovoTempoFilter = "pago"; mobileNovoTempoPage = 0; renderizarAlertasNovoTempo(status, aberto, atraso, destino, consulta); });

        int paginas = Math.max(1, (filtrados.size() + MOBILE_BOLETOS_PAGE_SIZE - 1) / MOBILE_BOLETOS_PAGE_SIZE);
        mobileNovoTempoPage = Math.min(mobileNovoTempoPage, paginas - 1);
        int inicio = mobileNovoTempoPage * MOBILE_BOLETOS_PAGE_SIZE;
        int fim = Math.min(filtrados.size(), inicio + MOBILE_BOLETOS_PAGE_SIZE);
        for (int i = inicio; i < fim; i++) destino.addView(cartaoAlertaNovoTempo(filtrados.get(i), status, aberto, atraso, destino, consulta));
        if (filtrados.isEmpty()) destino.addView(texto("Nenhuma venda " + ("pago".equals(mobileNovoTempoFilter) ? "paga" : "pendente") + " encontrada.", 14, false));
        else adicionarPaginacaoBoletos(destino, filtrados.size(), mobileNovoTempoPage,
            () -> { mobileNovoTempoPage--; renderizarAlertasNovoTempo(status, aberto, atraso, destino, consulta); },
            () -> { mobileNovoTempoPage++; renderizarAlertasNovoTempo(status, aberto, atraso, destino, consulta); });
    }

    private View cartaoAlertaNovoTempo(JSONObject row, TextView status, TextView aberto, TextView atraso, LinearLayout destino, String consulta) {
        LinearLayout card = coluna();
        card.setPadding(dp(14), dp(12), dp(14), dp(12));
        card.setBackground(fundoComBorda(Color.WHITE, Color.rgb(216, 227, 220), 9));
        LinearLayout.LayoutParams cp = new LinearLayout.LayoutParams(-1, -2);
        cp.setMargins(0, dp(8), 0, 0);
        TextView cliente = texto(row.optString("client", "NOVO TEMPO"), 16, true);
        card.addView(cliente);
        String nf = row.optString("nf_number", "").trim();
        String venda = nf.isEmpty() ? "Venda" : "NF " + nf;
        card.addView(texto(venda + " · " + formatarDataBoleto(row.optString("sale_date", "")) + " " + row.optString("sale_time", ""), 13, false));
        card.addView(texto(moeda.format(row.optDouble("total", 0)) + " · " + row.optInt("item_count", 0) + " item(ns)", 16, true));
        boolean pago = "pago".equalsIgnoreCase(row.optString("status", "pendente"));
        boolean iniciou = row.optBoolean("notifications_due", false);
        boolean entregue = row.optBoolean("delivered", false);
        String statusLinha = pago ? "PAGO" : !entregue ? "AGUARDANDO ENTREGA" : iniciou ? "PENDENTE · " + row.optInt("hours_pending", 0) + "h" : "AGUARDANDO 24H";
        TextView chip = texto(statusLinha, 12, true);
        chip.setTextColor(pago ? Color.rgb(21, 101, 52) : iniciou ? Color.rgb(180, 35, 24) : Color.rgb(130, 82, 0));
        card.addView(chip);
        String alerta = !entregue ? "O prazo de 24h começa quando a nota for marcada como entregue."
            : iniciou ? "Próximo aviso " + dataHoraAlertaNovoTempo(row.optString("next_alert_at", ""))
            : "Avisos começam " + dataHoraAlertaNovoTempo(row.optString("alert_starts_at", "")) + " · 24h após a entrega";
        card.addView(texto(pago ? "Cobrança baixada" : alerta, 12, false));
        Button acao = botao(pago ? "Reabrir pendente" : "✓  Marcar como pago", pago ? Color.rgb(100, 116, 135) : Color.rgb(21, 101, 52));
        card.addView(acao);
        acao.setOnClickListener(v -> {
            acao.setEnabled(false);
            JSONObject body = new JSONObject();
            try {
                body.put("company_key", row.optString("company_key", "raios"));
                body.put("status", pago ? "pendente" : "pago");
            } catch (Exception ignored) { }
            new Thread(() -> {
                try {
                    enviarObjetoApi("/api/mobile/new-tempo/collections/" + row.optString("id"), "PUT", body);
                    runOnUiThread(() -> {
                        try {
                            row.put("status", pago ? "pendente" : "pago");
                            if (!pago) row.put("paid_at", new java.text.SimpleDateFormat("yyyy-MM-dd HH:mm", new Locale("pt", "BR")).format(new java.util.Date()));
                        } catch (Exception ignored) { }
                        aviso(pago ? "Cobrança reaberta." : "Venda marcada como paga.");
                        renderizarAlertasNovoTempo(status, aberto, atraso, destino, consulta);
                    });
                } catch (Exception e) {
                    runOnUiThread(() -> { acao.setEnabled(true); aviso("Não foi possível atualizar a cobrança."); });
                }
            }).start();
        });
        aplicarFeedbackToque(card);
        card.setTag(consulta);
        return card;
    }

    private String dataHoraAlertaNovoTempo(String valor) {
        if (valor == null || valor.trim().isEmpty()) return "horário a definir";
        String dataParte = valor.length() >= 10 ? formatarDataBoleto(valor.substring(0, 10)) : valor;
        String horaParte = valor.length() >= 16 ? valor.substring(11, 16) : "";
        return horaParte.isEmpty() ? dataParte : dataParte + " às " + horaParte;
    }

    private void atualizarTotaisBoletos(TextView aberto, TextView atraso, JSONObject respostaAtraso) {
        double total = 0;
        int quantidade = 0;
        for (int i = 0; i < mobileBoletoRows.length(); i++) {
            JSONObject boleto = mobileBoletoRows.optJSONObject(i);
            if (boleto == null || statusBoletoPago(boleto)) continue;
            total += boleto.optDouble("total_val", 0);
            quantidade++;
        }
        aberto.setText("Em aberto · " + quantidade + "\n" + moeda.format(total));
        atraso.setText("Em atraso · " + respostaAtraso.optInt("count", 0) + "\n" + moeda.format(respostaAtraso.optDouble("total_value", 0)));
        atraso.setTextColor(respostaAtraso.optInt("count", 0) > 0 ? Color.rgb(185, 28, 28) : Color.rgb(20, 83, 45));
    }

    private void renderizarCarteiraBoletos(TextView status, TextView aberto, TextView atraso, LinearLayout destino, String consulta) {
        destino.removeAllViews();
        String filtro = semAcento(consulta == null ? "" : consulta.trim()).toLowerCase(new Locale("pt", "BR"));
        java.util.ArrayList<JSONObject> encontrados = new java.util.ArrayList<>();
        for (int i = 0; i < mobileBoletoRows.length(); i++) {
            JSONObject boleto = mobileBoletoRows.optJSONObject(i);
            if (boleto == null) continue;
            boolean pago = statusBoletoPago(boleto);
            boolean vencido = !pago && boleto.optBoolean("is_overdue", false);
            if ("pago".equals(mobileBoletoStatusFilter) != pago) continue;
            if ("vencido".equals(mobileBoletoStatusFilter) != vencido && !"pago".equals(mobileBoletoStatusFilter)) continue;
            String cliente = boleto.optString("client", "Cliente");
            String nf = boleto.optString("nf_number", "").trim();
            if (!semAcento(cliente + " " + nf).toLowerCase(new Locale("pt", "BR")).contains(filtro)) continue;
            encontrados.add(boleto);
        }
        int total = encontrados.size();
        int paginas = Math.max(1, (total + MOBILE_BOLETOS_PAGE_SIZE - 1) / MOBILE_BOLETOS_PAGE_SIZE);
        mobileBoletoPage = Math.min(mobileBoletoPage, paginas - 1);
        if (total == 0) {
            String mensagem = "vencido".equals(mobileBoletoStatusFilter) ? "Nenhum boleto em atraso para os clientes acompanhados." : "Nenhum boleto nesta lista.";
            destino.addView(texto(mensagem, 13, false));
        } else {
            int inicio = mobileBoletoPage * MOBILE_BOLETOS_PAGE_SIZE;
            int fim = Math.min(inicio + MOBILE_BOLETOS_PAGE_SIZE, total);
            for (int i = inicio; i < fim; i++) {
                JSONObject boleto = encontrados.get(i);
                boolean pago = statusBoletoPago(boleto);
                destino.addView(cartaoBoleto(boleto, pago, !pago && boleto.optBoolean("is_overdue", false)));
            }
            adicionarPaginacaoBoletos(destino, total, mobileBoletoPage,
                    () -> { mobileBoletoPage--; renderizarCarteiraBoletos(status, aberto, atraso, destino, consulta); },
                    () -> { mobileBoletoPage++; renderizarCarteiraBoletos(status, aberto, atraso, destino, consulta); });
        }
    }

    private View cartaoBoleto(JSONObject boleto, boolean pago, boolean vencido) {
        LinearLayout card = coluna();
        card.setPadding(dp(12), dp(9), dp(12), dp(9));
        card.setBackground(fundoComBorda(Color.WHITE, Color.rgb(216, 227, 220), 10));
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-1, -2);
        params.setMargins(0, dp(4), 0, dp(4));
        card.setLayoutParams(params);
        String nf = boleto.optString("nf_number", "").trim();
        String identificacao = boleto.optString("client", "Cliente") + (nf.isEmpty() ? "" : " · NF " + nf);
        TextView cliente = texto(identificacao, 14, true);
        card.addView(cliente);
        String vencimento = valorTextoBoleto(boleto, "due_date");
        String linha = vencimento.isEmpty() ? "Vencimento não cadastrado" : "Vencimento " + formatarDataBoleto(vencimento);
        linha += " · " + moeda.format(boleto.optDouble("total_val", 0));
        card.addView(texto(linha, 12, false));
        TextView estado = texto(pago ? "Pago" : vencido ? "Em atraso" : "A vencer", 11, true);
        estado.setTextColor(pago ? Color.rgb(21, 101, 52) : vencido ? Color.rgb(185, 28, 28) : Color.rgb(71, 85, 105));
        card.addView(estado);

        LinearLayout acoes = new LinearLayout(this);
        acoes.setOrientation(LinearLayout.HORIZONTAL);
        acoes.setGravity(Gravity.CENTER_VERTICAL);
        Button vencimentoBtn = botao(vencimento.isEmpty() ? "Definir vencimento" : "Alterar vencimento", Color.rgb(240, 245, 241));
        vencimentoBtn.setTextColor(Color.rgb(20, 83, 45));
        vencimentoBtn.setTextSize(11);
        Button statusBtn = botao(pago ? "Reabrir pendente" : "Marcar como pago", pago ? Color.rgb(100, 116, 139) : Color.rgb(21, 101, 52));
        statusBtn.setTextSize(11);
        LinearLayout.LayoutParams vencimentoParams = new LinearLayout.LayoutParams(0, dp(40), 1);
        vencimentoParams.setMargins(0, dp(3), dp(5), 0);
        acoes.addView(vencimentoBtn, vencimentoParams);
        LinearLayout.LayoutParams statusParams = new LinearLayout.LayoutParams(0, dp(40), 1);
        statusParams.setMargins(dp(5), dp(3), 0, 0);
        acoes.addView(statusBtn, statusParams);
        card.addView(acoes);
        vencimentoBtn.setOnClickListener(v -> escolherVencimentoBoleto(boleto));
        statusBtn.setOnClickListener(v -> alterarStatusBoleto(boleto, pago));
        return card;
    }

    private void escolherVencimentoBoleto(JSONObject boleto) {
        Calendar data = Calendar.getInstance();
        String atual = valorTextoBoleto(boleto, "due_date");
        if (atual.isEmpty()) atual = valorTextoBoleto(boleto, "sale_date");
        try {
            if (atual.matches("\\d{4}-\\d{2}-\\d{2}")) {
                String[] partes = atual.split("-");
                data.set(Integer.parseInt(partes[0]), Integer.parseInt(partes[1]) - 1, Integer.parseInt(partes[2]));
            }
        } catch (Exception ignored) {}
        new DatePickerDialog(this, (view, ano, mes, dia) -> {
            JSONObject alteracoes = new JSONObject();
            try { alteracoes.put("due_date", String.format(Locale.US, "%04d-%02d-%02d", ano, mes + 1, dia)); }
            catch (Exception e) { aviso("Não foi possível preparar a data."); return; }
            salvarAlteracaoBoletoMobile(boleto, alteracoes, "Vencimento atualizado.");
        }, data.get(Calendar.YEAR), data.get(Calendar.MONTH), data.get(Calendar.DAY_OF_MONTH)).show();
    }

    private void alterarStatusBoleto(JSONObject boleto, boolean estaPago) {
        JSONObject alteracoes = new JSONObject();
        try {
            alteracoes.put("status", estaPago ? "pendente" : "pago");
            alteracoes.put("paid_date", estaPago ? JSONObject.NULL : new java.text.SimpleDateFormat("yyyy-MM-dd", Locale.US).format(new java.util.Date()));
        } catch (Exception e) { aviso("Não foi possível preparar a alteração do boleto."); return; }
        salvarAlteracaoBoletoMobile(boleto, alteracoes, estaPago ? "Boleto reaberto como pendente." : "Boleto marcado como pago.");
    }

    private void salvarAlteracaoBoletoMobile(JSONObject boleto, JSONObject alteracoes, String sucesso) {
        String id = valorTextoBoleto(boleto, "id");
        if (id.isEmpty()) { aviso("Este boleto não possui identificador válido."); return; }
        new Thread(() -> {
            try {
                enviarObjetoApi("/api/boletos/" + id, "PUT", alteracoes);
                runOnUiThread(() -> { aviso(sucesso); abrirModuloBoletos(); });
            } catch (Exception e) {
                runOnUiThread(() -> aviso("Não foi possível atualizar o boleto. Verifique a conexão e tente novamente."));
            }
        }).start();
    }

    private String valorTextoBoleto(JSONObject boleto, String chave) {
        Object valor = boleto == null ? null : boleto.opt(chave);
        if (valor == null || valor == JSONObject.NULL) return "";
        String texto = String.valueOf(valor).trim();
        return texto.isEmpty() || "null".equalsIgnoreCase(texto) || "none".equalsIgnoreCase(texto) ? "" : texto;
    }

    private String formatarDataBoleto(String data) {
        String valor = data == null ? "" : data.trim();
        if (valor.matches("\\d{4}-\\d{2}-\\d{2}.*")) valor = valor.substring(0, 10);
        if (valor.matches("\\d{4}-\\d{2}-\\d{2}")) return formatarDataIso(valor);
        if (valor.matches("\\d{2}/\\d{2}/\\d{4}")) return valor;
        return valor;
    }

    private void adicionarPaginacaoBoletos(LinearLayout destino, int total, int pagina, Runnable anterior, Runnable proxima) {
        int paginas = Math.max(1, (total + MOBILE_BOLETOS_PAGE_SIZE - 1) / MOBILE_BOLETOS_PAGE_SIZE);
        int inicio = pagina * MOBILE_BOLETOS_PAGE_SIZE + 1;
        int fim = Math.min((pagina + 1) * MOBILE_BOLETOS_PAGE_SIZE, total);
        LinearLayout controles = new LinearLayout(this);
        controles.setGravity(Gravity.CENTER_VERTICAL);
        controles.setPadding(0, dp(6), 0, dp(6));
        Button voltar = botao("‹ Anterior", Color.rgb(21, 101, 52));
        voltar.setTextSize(11);
        voltar.setTextColor(Color.WHITE);
        voltar.setEnabled(pagina > 0);
        if (pagina == 0) {
            voltar.setBackground(fundoArredondado(Color.rgb(232, 238, 234), 9));
            voltar.setTextColor(Color.rgb(91, 107, 96));
        }
        TextView resumo = texto(inicio + "–" + fim + " de " + total + " · página " + (pagina + 1) + "/" + paginas, 12, true);
        resumo.setGravity(Gravity.CENTER);
        Button avancar = botao("Próxima ›", Color.rgb(21, 101, 52));
        avancar.setTextSize(11);
        avancar.setTextColor(Color.WHITE);
        avancar.setEnabled(pagina + 1 < paginas);
        if (pagina + 1 >= paginas) {
            avancar.setBackground(fundoArredondado(Color.rgb(232, 238, 234), 9));
            avancar.setTextColor(Color.rgb(91, 107, 96));
        }
        controles.addView(voltar, new LinearLayout.LayoutParams(dp(102), dp(44)));
        controles.addView(resumo, new LinearLayout.LayoutParams(0, -2, 1));
        controles.addView(avancar, new LinearLayout.LayoutParams(dp(102), dp(44)));
        destino.addView(controles);
        voltar.setOnClickListener(v -> anterior.run());
        avancar.setOnClickListener(v -> proxima.run());
    }

    private boolean statusBoletoPago(JSONObject boleto) {
        String status = boleto.optString("status", "").trim();
        return "pago".equalsIgnoreCase(status) || "paid".equalsIgnoreCase(status);
    }

    private void abrirConfiguracaoBoletos() {
        temaEscuroAtivo = true;
        telaAtual = "boletos_clientes";
        LinearLayout tela = coluna();
        tela.setBackgroundColor(COR_FUNDO_ESCURO);
        ScrollView scroll = new ScrollView(this);
        LinearLayout conteudo = coluna();
        conteudo.setPadding(dp(18), dp(12), dp(18), dp(18));
        scroll.addView(conteudo);
        tela.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 1));

        TextView titulo = texto("Configurar clientes", 23, true);
        titulo.setTextColor(Color.rgb(20, 83, 45));
        conteudo.addView(titulo);
        conteudo.addView(texto("Marque as empresas cujos boletos quer acompanhar.", 13, false));
        TextView estado = texto("Carregando clientes...", 12, false);
        conteudo.addView(estado);
        TextView contagem = texto("Selecione as empresas que devem aparecer nas notificações.", 13, true);
        conteudo.addView(contagem);
        Switch alertas = new Switch(this);
        alertas.setText("Alertas de atraso\nNotificar sobre os clientes selecionados");
        alertas.setTextColor(COR_TEXTO_CLARO);
        alertas.setTextSize(13);
        alertas.setPadding(dp(12), dp(8), dp(12), dp(8));
        alertas.setBackground(fundoComBorda(Color.WHITE, Color.rgb(216, 227, 220), 10));
        conteudo.addView(alertas);
        EditText busca = campo("Buscar empresa...", InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS);
        conteudo.addView(busca);

        LinearLayout filtros = new LinearLayout(this);
        filtros.setOrientation(LinearLayout.HORIZONTAL);
        Button todos = botaoFiltroCliente("Todos", "todos");
        Button comBoletos = botaoFiltroCliente("Com boletos", "com_boletos");
        Button selecionados = botaoFiltroCliente("Selecionados", "selecionados");
        filtros.addView(todos, new LinearLayout.LayoutParams(0, dp(42), 1));
        filtros.addView(comBoletos, new LinearLayout.LayoutParams(0, dp(42), 1));
        filtros.addView(selecionados, new LinearLayout.LayoutParams(0, dp(42), 1));
        conteudo.addView(filtros);
        LinearLayout clientes = coluna();
        conteudo.addView(clientes);

        LinearLayout rodape = new LinearLayout(this);
        rodape.setPadding(dp(14), dp(8), dp(14), dp(8));
        rodape.setBackgroundColor(Color.WHITE);
        Button salvar = botao("Salvar seleção", Color.rgb(21, 101, 52));
        rodape.addView(salvar);
        tela.addView(rodape, new LinearLayout.LayoutParams(-1, -2));
        Runnable atualizarLista = () -> renderizarClientesBoleto(clientes, busca.getText().toString(), contagem);
        busca.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            @Override public void onTextChanged(CharSequence s, int start, int before, int count) { mobileBoletoClientPage = 0; atualizarLista.run(); }
            @Override public void afterTextChanged(Editable s) {}
        });
        todos.setOnClickListener(v -> {
            mobileBoletoClientFilter = "todos";
            mobileBoletoClientPage = 0;
            atualizarBotoesFiltroCliente(todos, comBoletos, selecionados);
            atualizarLista.run();
        });
        comBoletos.setOnClickListener(v -> {
            mobileBoletoClientFilter = "com_boletos";
            mobileBoletoClientPage = 0;
            atualizarBotoesFiltroCliente(todos, comBoletos, selecionados);
            atualizarLista.run();
        });
        selecionados.setOnClickListener(v -> {
            mobileBoletoClientFilter = "selecionados";
            mobileBoletoClientPage = 0;
            atualizarBotoesFiltroCliente(todos, comBoletos, selecionados);
            atualizarLista.run();
        });
        salvar.setOnClickListener(v -> salvarConfiguracaoBoletos(alertas, estado, salvar));
        setContentView(tela);
        carregarConfiguracaoBoletos(estado, alertas, clientes, contagem, busca);
    }

    private Button botaoFiltroCliente(String label, String filtro) {
        boolean ativo = filtro.equals(mobileBoletoClientFilter);
        Button botao = new Button(this);
        botao.setText(label);
        botao.setAllCaps(false);
        botao.setTextSize(11);
        botao.setTextColor(ativo ? Color.WHITE : Color.rgb(39, 57, 45));
        botao.setBackground(fundoComBorda(ativo ? Color.rgb(21, 101, 52) : Color.WHITE, ativo ? Color.rgb(21, 101, 52) : Color.rgb(216, 227, 220), 9));
        return botao;
    }

    private void atualizarBotoesFiltroCliente(Button todos, Button comBoletos, Button selecionados) {
        estilizarBotaoFiltroCliente(todos, "todos".equals(mobileBoletoClientFilter));
        estilizarBotaoFiltroCliente(comBoletos, "com_boletos".equals(mobileBoletoClientFilter));
        estilizarBotaoFiltroCliente(selecionados, "selecionados".equals(mobileBoletoClientFilter));
    }

    private void estilizarBotaoFiltroCliente(Button botao, boolean ativo) {
        int verde = Color.rgb(21, 101, 52);
        botao.setTextColor(ativo ? Color.WHITE : Color.rgb(39, 57, 45));
        botao.setBackground(fundoComBorda(ativo ? verde : Color.WHITE, ativo ? verde : Color.rgb(216, 227, 220), 9));
    }

    private void carregarConfiguracaoBoletos(TextView estado, Switch alertas, LinearLayout clientes, TextView contagem, EditText busca) {
        estado.setText("Carregando empresas acompanhadas...");
        new Thread(() -> {
            try {
                JSONObject config = buscarObjetoApi(MOBILE_BOLETOS_CONFIG_URL);
                JSONArray linhas = buscarArrayApi("/api/boletos");
                runOnUiThread(() -> {
                    mobileBoletoClients = config.optJSONArray("clients") == null ? new JSONArray() : config.optJSONArray("clients");
                    mobileBoletoRows = linhas;
                    mobileBoletoAlertEnabled = config.optBoolean("alert_enabled", true);
                    alertas.setChecked(mobileBoletoAlertEnabled);
                    estado.setText("A seleção é compartilhada com o ERP.");
                    renderizarClientesBoleto(clientes, busca.getText().toString(), contagem);
                });
            } catch (Exception e) {
                runOnUiThread(() -> estado.setText("Não foi possível carregar clientes. Verifique a conexão e tente novamente."));
            }
        }).start();
    }

    private void renderizarClientesBoleto(LinearLayout destino, String consulta, TextView contagem) {
        destino.removeAllViews();
        String filtro = semAcento(consulta == null ? "" : consulta.trim()).toLowerCase(new Locale("pt", "BR"));
        int selecionados = 0;
        java.util.ArrayList<Integer> filtrados = new java.util.ArrayList<>();
        for (int i = 0; i < mobileBoletoClients.length(); i++) {
            JSONObject cliente = mobileBoletoClients.optJSONObject(i);
            if (cliente == null) continue;
            boolean habilitado = cliente.optBoolean("enabled", false);
            if (habilitado) selecionados++;
            String nome = cliente.optString("name", "");
            if (!semAcento(nome).toLowerCase(new Locale("pt", "BR")).contains(filtro)) continue;
            int quantidade = 0;
            int atrasados = 0;
            for (int j = 0; j < mobileBoletoRows.length(); j++) {
                JSONObject boleto = mobileBoletoRows.optJSONObject(j);
                if (boleto == null || !semAcento(nome).equalsIgnoreCase(semAcento(boleto.optString("client", "")))) continue;
                quantidade++;
                if (!statusBoletoPago(boleto) && boleto.optBoolean("is_overdue", false)) atrasados++;
            }
            if ("selecionados".equals(mobileBoletoClientFilter) && !habilitado) continue;
            if ("com_boletos".equals(mobileBoletoClientFilter) && quantidade == 0) continue;
            filtrados.add(i);
        }
        int total = filtrados.size();
        int paginas = Math.max(1, (total + MOBILE_BOLETOS_PAGE_SIZE - 1) / MOBILE_BOLETOS_PAGE_SIZE);
        mobileBoletoClientPage = Math.min(mobileBoletoClientPage, paginas - 1);
        int inicio = mobileBoletoClientPage * MOBILE_BOLETOS_PAGE_SIZE;
        int fim = Math.min(inicio + MOBILE_BOLETOS_PAGE_SIZE, total);
        for (int posicao = inicio; posicao < fim; posicao++) {
            int i = filtrados.get(posicao);
            JSONObject cliente = mobileBoletoClients.optJSONObject(i);
            if (cliente == null) continue;
            boolean habilitado = cliente.optBoolean("enabled", false);
            String nome = cliente.optString("name", "");
            int quantidade = 0;
            int atrasados = 0;
            for (int j = 0; j < mobileBoletoRows.length(); j++) {
                JSONObject boleto = mobileBoletoRows.optJSONObject(j);
                if (boleto == null || !semAcento(nome).equalsIgnoreCase(semAcento(boleto.optString("client", "")))) continue;
                quantidade++;
                if (!statusBoletoPago(boleto) && boleto.optBoolean("is_overdue", false)) atrasados++;
            }
            CheckBox caixa = new CheckBox(this);
            caixa.setButtonTintList(android.content.res.ColorStateList.valueOf(Color.rgb(21, 128, 76)));
            caixa.setChecked(habilitado);
            LinearLayout textos = coluna();
            TextView nomeView = texto(nome, 14, true);
            nomeView.setSingleLine(true);
            nomeView.setEllipsize(android.text.TextUtils.TruncateAt.END);
            textos.addView(nomeView);
            String detalhe = !habilitado ? "Não selecionado" : quantidade + (quantidade == 1 ? " boleto" : " boletos") + (atrasados > 0 ? " · " + atrasados + " em atraso" : " · sem atrasos");
            textos.addView(texto(detalhe, 11, false));
            LinearLayout linha = new LinearLayout(this);
            linha.setOrientation(LinearLayout.HORIZONTAL);
            linha.setGravity(Gravity.CENTER_VERTICAL);
            linha.setPadding(dp(8), dp(5), dp(10), dp(5));
            linha.addView(caixa, new LinearLayout.LayoutParams(dp(44), dp(48)));
            linha.addView(textos, new LinearLayout.LayoutParams(0, -2, 1));
            LinearLayout.LayoutParams linhaParams = new LinearLayout.LayoutParams(-1, -2);
            linhaParams.setMargins(0, dp(2), 0, dp(2));
            destino.addView(linha, linhaParams);
            final int index = i;
            caixa.setOnCheckedChangeListener((button, checked) -> {
                try { mobileBoletoClients.getJSONObject(index).put("enabled", checked); }
                catch (Exception ignored) {}
                renderizarClientesBoleto(destino, consulta, contagem);
            });
            linha.setOnClickListener(v -> caixa.setChecked(!caixa.isChecked()));
        }
        contagem.setText(selecionados + " selecionados para notificações · " + total + " empresas nesta lista");
        if (total == 0) destino.addView(texto("Nenhuma empresa encontrada neste filtro.", 13, false));
        else adicionarPaginacaoBoletos(destino, total, mobileBoletoClientPage,
                () -> { mobileBoletoClientPage--; renderizarClientesBoleto(destino, consulta, contagem); },
                () -> { mobileBoletoClientPage++; renderizarClientesBoleto(destino, consulta, contagem); });
    }

    private void salvarConfiguracaoBoletos(Switch alertas, TextView estado, Button salvar) {
        JSONArray selecionados = new JSONArray();
        for (int i = 0; i < mobileBoletoClients.length(); i++) {
            JSONObject cliente = mobileBoletoClients.optJSONObject(i);
            if (cliente != null && cliente.optBoolean("enabled", false)) selecionados.put(cliente.optString("name", ""));
        }
        JSONObject body = new JSONObject();
        try {
            body.put("enabled", selecionados);
            body.put("alert_enabled", alertas.isChecked());
        } catch (Exception e) {
            aviso("Não foi possível preparar a seleção de clientes.");
            return;
        }
        salvar.setEnabled(false);
        estado.setText("Salvando seleção...");
        new Thread(() -> {
            try {
                enviarObjetoApi(MOBILE_BOLETOS_CONFIG_URL, "PUT", body);
                mobileBoletoAlertEnabled = alertas.isChecked();
                runOnUiThread(() -> {
                    aviso("Seleção salva: " + selecionados.length() + " empresa(s).");
                    abrirModuloBoletos();
                });
            } catch (Exception e) {
                runOnUiThread(() -> {
                    salvar.setEnabled(true);
                    estado.setText("Falha ao salvar. Verifique a conexão e tente novamente.");
                });
            }
        }).start();
    }

    private void abrirModuloProjecao(String dias, String produtoFiltro, String fonteFiltro, String visualizacao) {
        temaEscuroAtivo = true;
        telaAtual = "projecao";
        ScrollView scroll = new ScrollView(this);
        scroll.setBackgroundColor(COR_FUNDO_ESCURO);
        LinearLayout raiz = coluna();
        raiz.setBackgroundColor(COR_FUNDO_ESCURO);
        raiz.setPadding(dp(18), dp(18), dp(18), dp(28));
        scroll.addView(raiz);
        adicionarCabecalhoModulo(raiz, "Projeção", "Estimativa de saída com base no histórico real.");
        adicionarBannerModulo(raiz, "PLANEJAMENTO", "Antecipe a saída dos produtos", "Compare períodos e veja tendências antes de organizar as próximas compras.", Color.rgb(37, 99, 235));

        LinearLayout filtrosPeriodo = new LinearLayout(this);
        filtrosPeriodo.setOrientation(LinearLayout.HORIZONTAL);
        filtrosPeriodo.addView(botaoFiltro("7 dias", "7".equals(dias), () -> abrirModuloProjecao("7", produtoFiltro, fonteFiltro, visualizacao)), paramsFiltro(0));
        filtrosPeriodo.addView(botaoFiltro("15 dias", "15".equals(dias), () -> abrirModuloProjecao("15", produtoFiltro, fonteFiltro, visualizacao)), paramsFiltro(1));
        filtrosPeriodo.addView(botaoFiltro("30 dias", "30".equals(dias), () -> abrirModuloProjecao("30", produtoFiltro, fonteFiltro, visualizacao)), paramsFiltro(2));
        raiz.addView(filtrosPeriodo);

        EditText produtoBusca = campo("Produto (opcional)", InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS);
        produtoBusca.setText(produtoFiltro == null ? "" : produtoFiltro);
        raiz.addView(produtoBusca);

        Spinner fonte = new Spinner(this);
        String[] fontes = {"Geral", "Cliente", "Entregador", "Tipo", "Origem"};
        fonte.setAdapter(new ArrayAdapter<>(this, android.R.layout.simple_spinner_dropdown_item, fontes));
        selecionarSpinner(fonte, fonteFiltro);
        raiz.addView(texto("Fonte", 13, false));
        raiz.addView(fonte);

        Spinner view = new Spinner(this);
        String[] views = {"Consolidada", "Produto"};
        view.setAdapter(new ArrayAdapter<>(this, android.R.layout.simple_spinner_dropdown_item, views));
        selecionarSpinner(view, visualizacao);
        raiz.addView(texto("Visualização", 13, false));
        raiz.addView(view);

        TextView resumo = texto("Carregando projeção...", 15, true);
        resumo.setGravity(Gravity.CENTER_HORIZONTAL);
        raiz.addView(resumo);
        LinearLayout lista = coluna();
        raiz.addView(lista);

        final String[] exportarTexto = {""};
        Button atualizar = botao("Atualizar", Color.rgb(37, 99, 235));
        atualizar.setOnClickListener(v -> carregarProjecao(dias, produtoBusca.getText().toString().trim(), valorFiltroSpinner(fonte), valorFiltroSpinner(view), resumo, lista, atualizar, exportarTexto));
        raiz.addView(atualizar);
        Button exportar = botao("Compartilhar resumo", Color.rgb(255, 255, 255));
        exportar.setTextColor(Color.rgb(20, 83, 45));
        exportar.setBackground(fundoComBorda(Color.WHITE, Color.rgb(216, 227, 220), 11));
        exportar.setOnClickListener(v -> compartilharTexto(exportarTexto[0].isEmpty() ? "Projeção ainda não carregada." : exportarTexto[0]));
        raiz.addView(exportar);
        setContentView(scroll);
        carregarProjecao(dias, produtoFiltro, fonteFiltro, visualizacao, resumo, lista, atualizar, exportarTexto);
    }

    private void carregarProjecao(String dias, String produtoFiltro, String fonteFiltro, String visualizacao, TextView resumo, LinearLayout lista, Button atualizar, String[] exportarTexto) {
        lista.removeAllViews();
        resumo.setText("Carregando projeção...");
        atualizar.setEnabled(false);
        new Thread(() -> {
            try {
                JSONObject dados = buscarProjecaoApi(dias, produtoFiltro, fonteFiltro, visualizacao);
                JSONObject r = dados.optJSONObject("resumo");
                JSONArray produtosArr = dados.optJSONArray("produtos");
                JSONArray tendenciaArr = dados.optJSONArray("tendencia");
                runOnUiThread(() -> {
                    lista.removeAllViews();
                    JSONObject resumoObj = r == null ? new JSONObject() : r;
                    resumo.setText("Período: " + dias + " dias • Fonte: " + nomeFiltro(fonteFiltro, "Geral"));
                    double total = resumoObj.optDouble("total_vendido", 0);
                    double mediaDia = resumoObj.optDouble("media_dia", 0);
                    double proj7 = resumoObj.optDouble("proj_7", 0);
                    double proj15 = resumoObj.optDouble("proj_15", 0);
                    double proj30 = resumoObj.optDouble("proj_30", 0);
                    JSONObject maiorSaida = resumoObj.optJSONObject("produto_maior_saida");
                    JSONObject maiorVariacao = resumoObj.optJSONObject("produto_maior_variacao");
                    JSONObject maiorRisco = resumoObj.optJSONObject("produto_maior_risco");

                    lista.addView(cardLeitura("Resumo geral", "Total vendido: " + formatarNumero(total), "Média/dia: " + formatarNumero(mediaDia), "Fonte principal: " + resumoObj.optString("fonte_principal", "Geral"), Color.rgb(239, 246, 255)));
                    if (tendenciaArr != null && tendenciaArr.length() > 0) {
                        lista.addView(graficoLinhaAnimado("Tendência de saída", rotulosTendencia(tendenciaArr, 12), valoresTendencia(tendenciaArr, 12), Color.rgb(59, 130, 246), mediaDia));
                    }
                    lista.addView(graficoMeta("Realizado x meta projetada", total, Math.max(proj30, total), Color.rgb(59, 130, 246)));
                    lista.addView(linhaKpis(
                        cardLeitura("Projeção 7 dias", formatarNumero(proj7), "Estimativa curta", "", Color.rgb(240, 253, 244)),
                        cardLeitura("Projeção 15 dias", formatarNumero(proj15), "Meio período", "", Color.rgb(240, 253, 244))
                    ));
                    lista.addView(linhaKpis(
                        cardLeitura("Projeção 30 dias", formatarNumero(proj30), "Estimativa mensal", "", Color.rgb(240, 253, 244)),
                        cardLeitura("Risco de ruptura", maiorRisco == null ? "Sem risco" : maiorRisco.optString("produto", "Produto"), maiorRisco == null ? "Estável" : maiorRisco.optString("status", "estável"), "", Color.rgb(254, 242, 242))
                    ));
                    lista.addView(cardLeitura("Maior saída", maiorSaida == null ? "Sem produto" : maiorSaida.optString("produto", "Produto"), maiorSaida == null ? "" : "Qtd: " + formatarNumero(maiorSaida.optDouble("quantidade", 0)), maiorSaida == null ? "" : "Proj. 30d: " + formatarNumero(maiorSaida.optDouble("proj_30", 0)), Color.rgb(255, 247, 237)));
                    lista.addView(cardLeitura("Maior variação", maiorVariacao == null ? "Sem produto" : maiorVariacao.optString("produto", "Produto"), maiorVariacao == null ? "" : "Variação: " + formatarNumero(maiorVariacao.optDouble("comparacao_anterior", 0)) + "%", maiorVariacao == null ? "" : "Status: " + maiorVariacao.optString("status", "estável"), Color.rgb(255, 247, 237)));

                    lista.addView(texto("Produtos com maior saída", 19, true));
                    if (produtosArr == null || produtosArr.length() == 0) {
                        lista.addView(texto("Nenhum produto encontrado para os filtros.", 15, false));
                    } else {
                        double maiorQtd = 0;
                        for (int i = 0; i < produtosArr.length(); i++) {
                            JSONObject p = produtosArr.optJSONObject(i);
                            if (p != null) maiorQtd = Math.max(maiorQtd, p.optDouble("quantidade", p.optDouble("quantidade_vendida", 0)));
                        }
                        for (int i = 0; i < Math.min(8, produtosArr.length()); i++) {
                            JSONObject p = produtosArr.optJSONObject(i);
                            if (p == null) continue;
                            double qtdProduto = p.optDouble("quantidade", p.optDouble("quantidade_vendida", 0));
                            lista.addView(graficoBarra(p.optString("produto", "Produto") + " • " + formatarNumero(qtdProduto), qtdProduto, maiorQtd, Color.rgb(34, 197, 94)));
                            lista.addView(cardLeitura("Detalhe", "Média/dia: " + formatarNumero(p.optDouble("media_dia", 0)), "Proj. 30d: " + formatarNumero(p.optDouble("proj_30", p.optDouble("proj_30d", 0))), "Status: " + p.optString("status", "estável"), Color.rgb(248, 250, 252)));
                        }
                    }

                    lista.addView(texto("Tendência diária", 19, true));
                    if (tendenciaArr != null && tendenciaArr.length() > 0) {
                        int inicio = Math.max(0, tendenciaArr.length() - 7);
                        for (int i = inicio; i < tendenciaArr.length(); i++) {
                            JSONObject t = tendenciaArr.optJSONObject(i);
                            if (t != null) lista.addView(cardLeitura(dataBR(t.optString("data")), "Saída total: " + formatarNumero(t.optDouble("total", 0)), "", "", Color.rgb(248, 250, 252)));
                        }
                    } else {
                        lista.addView(texto("Sem tendência diária para exibir.", 15, false));
                    }

                    lista.addView(texto("Produtos em risco", 19, true));
                    int riscos = 0;
                    if (produtosArr != null) {
                        for (int i = 0; i < produtosArr.length(); i++) {
                            JSONObject p = produtosArr.optJSONObject(i);
                            if (p == null || !"ruptura".equalsIgnoreCase(p.optString("status"))) continue;
                            lista.addView(cardLeitura(p.optString("produto", "Produto"), "Status: ruptura", "Média/dia: " + formatarNumero(p.optDouble("media_dia", 0)), "Proj. 7d: " + formatarNumero(p.optDouble("proj_7", 0)), Color.rgb(254, 242, 242)));
                            if (++riscos >= 5) break;
                        }
                    }
                    if (riscos == 0) lista.addView(texto("Nenhum produto em risco forte no filtro atual.", 15, false));

                    exportarTexto[0] = "Projeção Menina dos Raios\n"
                        + "Período: " + dias + " dias\n"
                        + "Total vendido: " + formatarNumero(total) + "\n"
                        + "Média/dia: " + formatarNumero(mediaDia) + "\n"
                        + "Proj. 7d: " + formatarNumero(proj7) + "\n"
                        + "Proj. 15d: " + formatarNumero(proj15) + "\n"
                        + "Proj. 30d: " + formatarNumero(proj30);
                    atualizar.setEnabled(true);
                });
            } catch (Exception e) {
                runOnUiThread(() -> {
                    lista.removeAllViews();
                    resumo.setText("Não foi possível carregar a projeção.");
                    lista.addView(cardLeitura("Estrutura pronta", "Endpoint esperado: /api/projecao/producao", "A tela já está preparada para os dados reais do site.", e.getMessage(), Color.rgb(255, 247, 237)));
                    atualizar.setEnabled(true);
                });
            }
        }).start();
    }

    private JSONObject buscarProjecaoApi(String dias, String produtoFiltro, String fonteFiltro, String visualizacao) throws Exception {
        String endpoint = "/api/projecao/producao?days=" + URLEncoder.encode(dias == null || dias.isEmpty() ? "30" : dias, "UTF-8");
        if (produtoFiltro != null && !produtoFiltro.trim().isEmpty()) endpoint += "&product=" + URLEncoder.encode(produtoFiltro.trim(), "UTF-8");
        String fonte = normalizarFiltroApi(fonteFiltro);
        if (!fonte.isEmpty()) endpoint += "&source=" + URLEncoder.encode(fonte, "UTF-8");
        String view = normalizarViewApi(visualizacao);
        if (!view.isEmpty()) endpoint += "&view=" + URLEncoder.encode(view, "UTF-8");
        return buscarObjetoApi(endpoint);
    }

    private View linhaKpis(View esquerda, View direita) {
        LinearLayout linha = new LinearLayout(this);
        linha.setOrientation(LinearLayout.HORIZONTAL);
        LinearLayout.LayoutParams linhaParams = new LinearLayout.LayoutParams(-1, -2);
        linhaParams.setMargins(0, dp(4), 0, dp(4));
        linha.setLayoutParams(linhaParams);
        LinearLayout.LayoutParams esquerdaParams = new LinearLayout.LayoutParams(0, -2, 1);
        esquerdaParams.setMargins(0, 0, dp(4), 0);
        LinearLayout.LayoutParams direitaParams = new LinearLayout.LayoutParams(0, -2, 1);
        direitaParams.setMargins(dp(4), 0, 0, 0);
        linha.addView(esquerda, esquerdaParams);
        linha.addView(direita, direitaParams);
        return linha;
    }

    private View cardIndicador(String titulo, String valor, String detalhe, int cor) {
        LinearLayout card = coluna();
        card.setPadding(dp(11), dp(9), dp(9), dp(9));
        card.setBackground(fundoComBorda(COR_CARD_ESCURO, Color.rgb(216, 227, 220), 11));
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-1, -2);
        params.setMargins(0, dp(4), 0, dp(4));
        card.setLayoutParams(params);
        TextView rotulo = texto(titulo, 11, true);
        rotulo.setTextColor(COR_TEXTO_SUAVE);
        rotulo.setSingleLine(true);
        rotulo.setEllipsize(android.text.TextUtils.TruncateAt.END);
        card.addView(rotulo);
        TextView numero = texto(valor, 16, true);
        numero.setTextColor(cor);
        numero.setSingleLine(true);
        numero.setEllipsize(android.text.TextUtils.TruncateAt.END);
        card.addView(numero);
        TextView apoio = texto(detalhe, 10, false);
        apoio.setSingleLine(true);
        apoio.setEllipsize(android.text.TextUtils.TruncateAt.END);
        card.addView(apoio);
        return card;
    }

    private View cardResultadoLiquido(double valor) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.HORIZONTAL);
        card.setGravity(Gravity.CENTER_VERTICAL);
        card.setPadding(dp(14), dp(12), dp(14), dp(12));
        card.setBackground(fundoComBorda(Color.rgb(232, 243, 235), Color.rgb(187, 216, 195), 12));
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-1, -2);
        params.setMargins(0, dp(7), 0, dp(5));
        card.setLayoutParams(params);
        LinearLayout textos = coluna();
        TextView rotulo = texto("RESULTADO LÍQUIDO", 10, true);
        rotulo.setTextColor(Color.rgb(79, 105, 87));
        textos.addView(rotulo);
        TextView numero = texto(moeda.format(valor), 23, true);
        numero.setTextColor(Color.rgb(21, 101, 52));
        textos.addView(numero);
        TextView detalhe = texto("Vendas menos valor absoluto das avarias", 10, false);
        textos.addView(detalhe);
        card.addView(textos);
        return card;
    }

    private View linhaResumoMobile(String titulo, String detalhe, String valor, int cor) {
        LinearLayout linha = new LinearLayout(this);
        linha.setOrientation(LinearLayout.HORIZONTAL);
        linha.setGravity(Gravity.CENTER_VERTICAL);
        linha.setPadding(dp(10), dp(8), dp(10), dp(8));
        linha.setBackground(fundoComBorda(COR_CARD_ESCURO, Color.rgb(216, 227, 220), 10));
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-1, -2);
        params.setMargins(0, dp(3), 0, dp(3));
        linha.setLayoutParams(params);
        View marca = new View(this);
        marca.setBackground(fundoArredondado(cor, 8));
        linha.addView(marca, new LinearLayout.LayoutParams(dp(4), dp(31)));
        LinearLayout textos = coluna();
        textos.setPadding(dp(9), 0, dp(4), 0);
        TextView nome = texto(titulo, 12, true);
        nome.setSingleLine(true);
        nome.setEllipsize(android.text.TextUtils.TruncateAt.END);
        textos.addView(nome);
        TextView apoio = texto(detalhe, 10, false);
        apoio.setSingleLine(true);
        apoio.setEllipsize(android.text.TextUtils.TruncateAt.END);
        textos.addView(apoio);
        linha.addView(textos, new LinearLayout.LayoutParams(0, -2, 1));
        TextView total = texto(valor, 12, true);
        total.setTextColor(cor);
        total.setGravity(Gravity.END | Gravity.CENTER_VERTICAL);
        total.setSingleLine(true);
        linha.addView(total);
        return linha;
    }

    private View cartaoClienteMobile(JSONObject cliente) {
        String nome = nomeClienteMaiusculo(valorOuVazio(cliente.optString("name"), "Cliente"));
        String primeiro = nome.trim().isEmpty() ? "C" : nome.trim().substring(0, 1).toUpperCase(new Locale("pt", "BR"));
        String[] partes = nome.trim().split("\\s+");
        String sigla = primeiro;
        if (partes.length > 1) sigla += partes[partes.length - 1].substring(0, 1).toUpperCase(new Locale("pt", "BR"));
        String contato = cliente.optString("city", "").trim();
        if (contato.isEmpty()) contato = cliente.optString("phone", "").trim();
        if (contato.isEmpty()) contato = "Toque para ver cadastro e histórico";

        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.HORIZONTAL);
        card.setGravity(Gravity.CENTER_VERTICAL);
        card.setPadding(dp(11), dp(9), dp(9), dp(9));
        card.setBackground(fundoComBorda(COR_CARD_ESCURO, Color.rgb(216, 227, 220), 11));
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-1, -2);
        params.setMargins(0, dp(4), 0, dp(4));
        card.setLayoutParams(params);

        TextView avatar = new TextView(this);
        avatar.setText(sigla);
        avatar.setTextColor(Color.rgb(21, 101, 52));
        avatar.setTextSize(11);
        avatar.setTypeface(null, 1);
        avatar.setGravity(Gravity.CENTER);
        avatar.setBackground(fundoComBorda(Color.rgb(232, 243, 235), Color.rgb(187, 216, 195), 20));
        card.addView(avatar, new LinearLayout.LayoutParams(dp(38), dp(38)));

        LinearLayout textos = coluna();
        textos.setPadding(dp(10), 0, dp(5), 0);
        TextView titulo = texto(nome, 13, true);
        titulo.setSingleLine(true);
        titulo.setEllipsize(android.text.TextUtils.TruncateAt.END);
        textos.addView(titulo);
        TextView sub = texto(contato, 10, false);
        sub.setSingleLine(true);
        sub.setEllipsize(android.text.TextUtils.TruncateAt.END);
        textos.addView(sub);
        card.addView(textos, new LinearLayout.LayoutParams(0, -2, 1));
        TextView seta = texto("›", 23, true);
        seta.setTextColor(Color.rgb(21, 101, 52));
        card.addView(seta);
        aplicarFeedbackToque(card);
        return card;
    }

    private void selecionarSpinner(Spinner spinner, String valor) {
        if (spinner == null || valor == null) return;
        String alvo = valor.trim();
        for (int i = 0; i < spinner.getCount(); i++) {
            Object item = spinner.getItemAtPosition(i);
            if (item != null && item.toString().equalsIgnoreCase(alvo)) {
                spinner.setSelection(i);
                return;
            }
            if ("consolidada".equalsIgnoreCase(alvo) && item != null && "Consolidada".equalsIgnoreCase(item.toString())) {
                spinner.setSelection(i);
                return;
            }
        }
    }

    private String valorFiltroSpinner(Spinner spinner) {
        Object item = spinner == null ? null : spinner.getSelectedItem();
        return item == null ? "" : item.toString();
    }

    private String normalizarFiltroApi(String valor) {
        if (valor == null) return "";
        String v = semAcento(valor).toLowerCase(Locale.US).trim();
        if (v.equals("cliente")) return "cliente";
        if (v.equals("entregador")) return "entregador";
        if (v.equals("tipo")) return "tipo";
        if (v.equals("origem")) return "origem";
        return "";
    }

    private String normalizarViewApi(String valor) {
        if (valor == null) return "consolidada";
        String v = semAcento(valor).toLowerCase(Locale.US).trim();
        if (v.equals("produto")) return "produto";
        return "consolidada";
    }

    private String nomeFiltro(String valor, String padrao) {
        return valor == null || valor.trim().isEmpty() ? padrao : valor;
    }

    private String semAcento(String texto) {
        if (texto == null) return "";
        return Normalizer.normalize(texto, Normalizer.Form.NFD).replaceAll("\\p{InCombiningDiacriticalMarks}+", "");
    }

    private void compartilharTexto(String texto) {
        Intent intent = new Intent(Intent.ACTION_SEND);
        intent.setType("text/plain");
        intent.putExtra(Intent.EXTRA_TEXT, texto);
        try {
            startActivity(Intent.createChooser(intent, "Compartilhar"));
        } catch (Exception e) {
            aviso("Não foi possível compartilhar.");
        }
    }

    private void abrirModuloProdutividade(String periodo) {
        temaEscuroAtivo = true;
        telaAtual = "produtividade";
        ScrollView scroll = new ScrollView(this);
        scroll.setBackgroundColor(COR_FUNDO_ESCURO);
        LinearLayout raiz = coluna();
        raiz.setBackgroundColor(COR_FUNDO_ESCURO);
        raiz.setPadding(dp(18), dp(18), dp(18), dp(28));
        scroll.addView(raiz);
        adicionarCabecalhoModulo(raiz, "Produtividade", "Resumo simples do que foi produzido no período.");
        adicionarBannerModulo(raiz, "DESEMPENHO", "Acompanhe a produção por período", "Veja o total registrado, os dias ativos e os melhores resultados.", Color.rgb(22, 163, 74));
        adicionarFiltrosPeriodo(raiz, periodo, p -> abrirModuloProdutividade(p));
        TextView resumo = texto("Carregando produtividade...", 15, true);
        raiz.addView(resumo);
        LinearLayout lista = coluna();
        raiz.addView(lista);
        Button atualizar = botao("↻ Atualizar", Color.rgb(21, 101, 52));
        atualizar.setTextSize(13);
        atualizar.setOnClickListener(v -> carregarProdutividade(periodo, resumo, lista, atualizar));
        raiz.addView(atualizar);
        setContentView(scroll);
        carregarProdutividade(periodo, resumo, lista, atualizar);
    }

    private void carregarProdutividade(String periodo, TextView resumo, LinearLayout lista, Button atualizar) {
        lista.removeAllViews();
        resumo.setText("Carregando produtividade...");
        atualizar.setEnabled(false);
        new Thread(() -> {
            try {
                JSONArray rows = buscarSalesApi("", anoPeriodo(periodo), mesPeriodo(periodo), 800);
                LinkedHashMap<String, double[]> porDia = new LinkedHashMap<>();
                double total = 0;
                int registros = 0;
                for (int i = 0; i < rows.length(); i++) {
                    JSONObject r = rows.getJSONObject(i);
                    if (!dentroDoPeriodo(r.optString("sale_date"), periodo)) continue;
                    String tipo = r.optString("sale_type", "");
                    if ("AVARIA".equalsIgnoreCase(tipo)) continue;
                    String dia = r.optString("sale_date", "Sem data");
                    double valor = r.optDouble("total", 0);
                    double[] acc = porDia.containsKey(dia) ? porDia.get(dia) : new double[]{0, 0};
                    acc[0] += valor;
                    acc[1] += 1;
                    porDia.put(dia, acc);
                    total += valor;
                    registros++;
                }
                double totalFinal = total;
                int registrosFinal = registros;
                runOnUiThread(() -> {
                    lista.removeAllViews();
                    resumo.setText(nomePeriodo(periodo) + " · " + registrosFinal + " movimentação(ões)");
                    if (porDia.isEmpty()) {
                        lista.addView(texto("Nenhum dado encontrado para este período.", 15, false));
                    } else {
                        double mediaPorDia = totalFinal / Math.max(1, porDia.size());
                        lista.addView(linhaKpis(
                            cardIndicador("Produzido", moeda.format(totalFinal), registrosFinal + " registro(s)", Color.rgb(34, 197, 94)),
                            cardIndicador("Dias ativos", String.valueOf(porDia.size()), "Média " + moeda.format(mediaPorDia) + "/dia", Color.rgb(59, 130, 246))));
                        lista.addView(graficoBarrasAnimado("Produção diária", rotulosGraficoDia(porDia, 12), valoresGraficoDia(porDia, 12), Color.rgb(52, 190, 145), 0));
                        List<Map.Entry<String, double[]>> diasOrdenados = new ArrayList<>(porDia.entrySet());
                        Collections.sort(diasOrdenados, (a, b) -> Double.compare(b.getValue()[0], a.getValue()[0]));
                        TextView destaques = texto("Dias de maior produção", 15, true);
                        destaques.setPadding(0, dp(10), 0, dp(4));
                        lista.addView(destaques);
                        for (int i = 0; i < Math.min(5, diasOrdenados.size()); i++) {
                            Map.Entry<String, double[]> dia = diasOrdenados.get(i);
                            lista.addView(linhaResumoMobile(dataBR(dia.getKey()), (int) dia.getValue()[1] + " registro(s)", moeda.format(dia.getValue()[0]), Color.rgb(52, 190, 145)));
                        }
                    }
                    atualizar.setEnabled(true);
                });
            } catch (Exception e) {
                runOnUiThread(() -> {
                    lista.removeAllViews();
                    resumo.setText("Não foi possível carregar.");
                    lista.addView(cardLeitura("Produtividade indisponível", "Não foi possível atualizar os registros.", "Confira a conexão e tente novamente.", e.getMessage(), Color.rgb(255, 247, 237)));
                    atualizar.setEnabled(true);
                });
            }
        }).start();
    }

    private void abrirModuloAvarias(String periodo) {
        temaEscuroAtivo = true;
        telaAtual = "avarias";
        ScrollView scroll = new ScrollView(this);
        scroll.setBackgroundColor(COR_FUNDO_ESCURO);
        LinearLayout raiz = coluna();
        raiz.setBackgroundColor(COR_FUNDO_ESCURO);
        raiz.setPadding(dp(18), dp(18), dp(18), dp(28));
        scroll.addView(raiz);
        adicionarCabecalhoModulo(raiz, "Avarias", "Leitura das ocorrências registradas no sistema.");
        adicionarBannerModulo(raiz, "CONTROLE DE PERDAS", "Registre e acompanhe avarias", "Informe produto, quantidade, valor e responsável. Os registros ficam sincronizados com o ERP.", Color.rgb(185, 55, 45));
        adicionarFiltrosPeriodo(raiz, periodo, p -> abrirModuloAvarias(p));
        Button inserirAvaria = botao("＋ Inserir avaria", Color.rgb(185, 55, 45));
        LinearLayout.LayoutParams inserirParams = new LinearLayout.LayoutParams(-1, dp(50));
        inserirParams.setMargins(0, dp(6), 0, dp(10));
        raiz.addView(inserirAvaria, inserirParams);
        inserirAvaria.setOnClickListener(v -> abrirFormularioAvaria(periodo));
        TextView resumo = texto("Carregando avarias...", 15, true);
        resumo.setGravity(Gravity.CENTER_HORIZONTAL);
        raiz.addView(resumo);
        LinearLayout lista = coluna();
        raiz.addView(lista);
        Button atualizar = botao("↻ Atualizar", Color.rgb(21, 101, 52));
        atualizar.setTextSize(13);
        atualizar.setOnClickListener(v -> carregarAvarias(periodo, resumo, lista, atualizar));
        raiz.addView(atualizar);
        setContentView(scroll);
        carregarAvarias(periodo, resumo, lista, atualizar);
    }

    private void abrirFormularioAvaria(String periodoRetorno) {
        aviso("Carregando responsáveis...");
        new Thread(() -> {
            try {
                JSONArray vendedores = buscarArrayApi("/api/sellers?module_context=avaria");
                runOnUiThread(() -> mostrarFormularioAvaria(vendedores, periodoRetorno));
            } catch (Exception e) {
                runOnUiThread(() -> aviso("Não foi possível carregar os responsáveis do ERP: " + mensagemErroSimples(e)));
            }
        }).start();
    }

    private void mostrarFormularioAvaria(JSONArray vendedores, String periodoRetorno) {
        if (vendedores == null || vendedores.length() == 0) { aviso("Cadastre um responsável ativo no ERP antes de lançar uma avaria."); return; }
        LinearLayout form = coluna(); form.setPadding(dp(18), dp(5), dp(18), dp(5));
        EditText clienteAvaria = campo("Cliente / estabelecimento", InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_CAP_CHARACTERS);
        EditText produtoAvaria = campo("Produto avariado", InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_CAP_SENTENCES);
        EditText quantidadeAvaria = campo("Quantidade", InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_FLAG_DECIMAL);
        quantidadeAvaria.setKeyListener(DigitsKeyListener.getInstance("0123456789,."));
        Spinner unidadeAvaria = new Spinner(this); unidadeAvaria.setAdapter(adaptadorSpinner(new String[]{"UN", "KG", "CX", "MC", "SC"}));
        EditText valorAvaria = campo("Valor unitário (R$)", InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_FLAG_DECIMAL);
        valorAvaria.setKeyListener(DigitsKeyListener.getInstance("0123456789,."));
        EditText motivoAvaria = campo("Motivo / observação", InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_CAP_SENTENCES);
        EditText dataAvaria = campo("Data da ocorrência", InputType.TYPE_CLASS_DATETIME);
        dataAvaria.setFocusable(false);
        dataAvaria.setText(new SimpleDateFormat("dd/MM/yyyy", new Locale("pt", "BR")).format(Calendar.getInstance().getTime()));
        dataAvaria.setOnClickListener(v -> {
            Calendar c = Calendar.getInstance();
            new DatePickerDialog(this, (picker, year, month, day) -> dataAvaria.setText(String.format(new Locale("pt", "BR"), "%02d/%02d/%04d", day, month + 1, year)), c.get(Calendar.YEAR), c.get(Calendar.MONTH), c.get(Calendar.DAY_OF_MONTH)).show();
        });
        Spinner responsavel = new Spinner(this);
        List<String> responsaveis = new ArrayList<>();
        for (int i = 0; i < vendedores.length(); i++) { JSONObject row = vendedores.optJSONObject(i); if (row != null) responsaveis.add(row.optString("name", "Responsável")); }
        responsavel.setAdapter(adaptadorSpinner(responsaveis));
        form.addView(rotuloCampo("CLIENTE")); form.addView(clienteAvaria);
        form.addView(rotuloCampo("PRODUTO")); form.addView(produtoAvaria);
        LinearLayout linhaQtd = new LinearLayout(this); linhaQtd.setOrientation(LinearLayout.HORIZONTAL);
        LinearLayout qtdCol = coluna(); qtdCol.addView(rotuloCampo("QUANTIDADE")); qtdCol.addView(quantidadeAvaria);
        LinearLayout unCol = coluna(); unCol.addView(rotuloCampo("UNIDADE")); unCol.addView(unidadeAvaria);
        linhaQtd.addView(qtdCol, new LinearLayout.LayoutParams(0, -2, 1));
        LinearLayout.LayoutParams unParams = new LinearLayout.LayoutParams(0, -2, 1); unParams.setMargins(dp(8), 0, 0, 0); linhaQtd.addView(unCol, unParams);
        form.addView(linhaQtd);
        form.addView(rotuloCampo("VALOR UNITÁRIO (R$)")); form.addView(valorAvaria);
        form.addView(rotuloCampo("DATA")); form.addView(dataAvaria);
        form.addView(rotuloCampo("RESPONSÁVEL")); form.addView(responsavel);
        form.addView(rotuloCampo("MOTIVO / OBSERVAÇÃO")); form.addView(motivoAvaria);
        ScrollView scroll = new ScrollView(this); scroll.setFillViewport(false); scroll.addView(form);
        AlertDialog dialog = new AlertDialog.Builder(this).setTitle("Registrar avaria")
            .setView(scroll).setNegativeButton("Cancelar", null).setPositiveButton("Salvar no ERP", null).create();
        dialog.setOnShowListener(ignored -> dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(button -> {
            String productName = produtoAvaria.getText().toString().trim();
            String clientName = clienteAvaria.getText().toString().trim();
            double qty, unitPrice;
            try { qty = Double.parseDouble(quantidadeAvaria.getText().toString().replace(',', '.')); } catch (Exception e) { qty = 0; }
            try { unitPrice = Double.parseDouble(valorAvaria.getText().toString().replace(',', '.')); } catch (Exception e) { unitPrice = 0; }
            int index = responsavel.getSelectedItemPosition();
            JSONObject seller = vendedores.optJSONObject(index);
            if (clientName.isEmpty() || productName.isEmpty() || qty <= 0 || seller == null) { aviso("Informe cliente, produto, quantidade e responsável."); return; }
            JSONObject body = new JSONObject();
            try {
                body.put("sale_type", "AVARIA"); body.put("sale_date", dataApiBR(dataAvaria.getText().toString()));
                body.put("client", nomeClienteMaiusculo(clientName)); body.put("product", productName);
                body.put("quantity", qty); body.put("unit_price", unitPrice); body.put("total", qty * unitPrice);
                body.put("notes", motivoAvaria.getText().toString().trim()); body.put("delivery_person", seller.optString("name"));
                body.put("seller_id", seller.optString("id")); body.put("source", "mobile"); body.put("plate", ""); body.put("nf_number", "");
            } catch (Exception e) { aviso("Não foi possível preparar o lançamento."); return; }
            button.setEnabled(false);
            new Thread(() -> {
                try {
                    enviarObjetoApi("/api/sales", "POST", body);
                    runOnUiThread(() -> { dialog.dismiss(); aviso("Avaria registrada no ERP."); abrirModuloAvarias(periodoRetorno); });
                } catch (Exception e) { runOnUiThread(() -> { button.setEnabled(true); aviso("Avaria não registrada: " + mensagemErroSimples(e)); }); }
            }).start();
        }));
        dialog.show();
    }

    private void carregarAvarias(String periodo, TextView resumo, LinearLayout lista, Button atualizar) {
        lista.removeAllViews();
        resumo.setText("Carregando avarias...");
        atualizar.setEnabled(false);
        new Thread(() -> {
            try {
                JSONArray rows = buscarSalesApi("AVARIA", anoPeriodo(periodo), mesPeriodo(periodo), 300);
                double total = 0;
                int qtd = 0;
                List<JSONObject> filtrados = new ArrayList<>();
                LinkedHashMap<String, double[]> porDia = new LinkedHashMap<>();
                for (int i = 0; i < rows.length(); i++) {
                    JSONObject r = rows.getJSONObject(i);
                    if (!dentroDoPeriodo(r.optString("sale_date"), periodo)) continue;
                    filtrados.add(r);
                    double valor = Math.abs(r.optDouble("total", 0));
                    total += valor;
                    String dia = r.optString("sale_date", "Sem data");
                    double[] acc = porDia.containsKey(dia) ? porDia.get(dia) : new double[]{0, 0};
                    acc[0] += valor;
                    acc[1] += 1;
                    porDia.put(dia, acc);
                    qtd++;
                }
                double totalFinal = total;
                int qtdFinal = qtd;
                runOnUiThread(() -> {
                    lista.removeAllViews();
                    resumo.setText(qtdFinal + " ocorrência(s) • " + moeda.format(totalFinal));
                    if (filtrados.isEmpty()) {
                        lista.addView(texto("Nenhuma avaria encontrada para este período.", 15, false));
                    } else {
                        lista.addView(graficoBarrasAnimado("Avarias por dia", rotulosGraficoDia(porDia, 12), valoresGraficoDia(porDia, 12), Color.rgb(239, 68, 68), 0));
                        for (JSONObject r : filtrados) {
                            String titulo = r.optString("product", "Produto") + " • " + r.optString("client", "Cliente");
                            String linha1 = "Data: " + dataBR(r.optString("sale_date")) + " • Qtd: " + formatarNumero(Math.abs(r.optDouble("quantity", 0)));
                            String linha2 = "Valor: " + moeda.format(Math.abs(r.optDouble("total", 0)));
                            String linha3 = r.optString("delivery_person", "").isEmpty() ? r.optString("notes", "Sem motivo informado") : "Responsável: " + r.optString("delivery_person");
                            lista.addView(cardLeitura(titulo, linha1, linha2, linha3, Color.rgb(254, 242, 242)));
                        }
                    }
                    atualizar.setEnabled(true);
                });
            } catch (Exception e) {
                runOnUiThread(() -> {
                    lista.removeAllViews();
                    resumo.setText("Não foi possível carregar.");
                    lista.addView(cardLeitura("Dados demonstrativos", "Endpoint esperado: /api/sales?sale_type=AVARIA", "A tela já está pronta para receber as ocorrências.", e.getMessage(), Color.rgb(255, 247, 237)));
                    atualizar.setEnabled(true);
                });
            }
        }).start();
    }

    private void abrirModuloClientes(String busca) {
        temaEscuroAtivo = true;
        telaAtual = "clientes";
        ScrollView scroll = new ScrollView(this);
        scroll.setBackgroundColor(COR_FUNDO_ESCURO);
        LinearLayout raiz = coluna();
        raiz.setBackgroundColor(COR_FUNDO_ESCURO);
        raiz.setPadding(dp(18), dp(18), dp(18), dp(28));
        scroll.addView(raiz);
        adicionarCabecalhoModulo(raiz, "Clientes", "Encontre um cadastro e abra o histórico de compras.");
        EditText campoBusca = campo("Nome, telefone, CNPJ ou e-mail", InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS);
        campoBusca.setText(busca == null ? "" : busca);
        raiz.addView(campoBusca);
        Button buscar = botao("Buscar", Color.rgb(37, 99, 235));
        raiz.addView(buscar);
        TextView resumo = texto("Carregando clientes...", 13, true);
        raiz.addView(resumo);
        LinearLayout lista = coluna();
        raiz.addView(lista);
        Button voltar = botao("Voltar para Home", Color.rgb(37, 99, 235));
        voltar.setOnClickListener(v -> mostrarHomeModulos());
        raiz.addView(voltar);
        buscar.setOnClickListener(v -> carregarClientes(campoBusca.getText().toString().trim(), resumo, lista, buscar));
        setContentView(scroll);
        carregarClientes(busca == null ? "" : busca, resumo, lista, buscar);
    }

    private void carregarClientes(String busca, TextView resumo, LinearLayout lista, Button buscar) {
        lista.removeAllViews();
        resumo.setText("Carregando clientes...");
        buscar.setEnabled(false);
        new Thread(() -> {
            try {
                JSONArray rows = buscarClientesApi(busca);
                runOnUiThread(() -> {
                    lista.removeAllViews();
                    resumo.setText(rows.length() + " cliente(s) encontrado(s)");
                    if (rows.length() == 0) {
                        lista.addView(texto("Nenhum cliente encontrado.", 15, false));
                    }
                    for (int i = 0; i < rows.length(); i++) {
                        JSONObject c = rows.optJSONObject(i);
                        if (c == null) continue;
                        View card = cartaoClienteMobile(c);
                        card.setOnClickListener(v -> abrirDetalheCliente(c));
                        lista.addView(card);
                    }
                    buscar.setEnabled(true);
                });
            } catch (Exception e) {
                runOnUiThread(() -> {
                    lista.removeAllViews();
                    resumo.setText("Não foi possível carregar.");
                    lista.addView(cardLeitura("Clientes indisponíveis", "Não foi possível atualizar a lista.", "Confira a conexão e tente novamente.", e.getMessage(), Color.rgb(255, 247, 237)));
                    buscar.setEnabled(true);
                });
            }
        }).start();
    }

    private void abrirDetalheCliente(JSONObject clienteJson) {
        temaEscuroAtivo = true;
        telaAtual = "cliente_detalhe";
        ScrollView scroll = new ScrollView(this);
        scroll.setBackgroundColor(COR_FUNDO_ESCURO);
        LinearLayout raiz = coluna();
        raiz.setBackgroundColor(COR_FUNDO_ESCURO);
        raiz.setPadding(dp(18), dp(18), dp(18), dp(28));
        scroll.addView(raiz);
        adicionarCabecalhoModulo(raiz, nomeClienteMaiusculo(clienteJson.optString("name", "Cliente")), "Detalhes e histórico resumido.");
        raiz.addView(cardLeitura("Cadastro", documentoCliente(clienteJson), "Telefone: " + valorOuVazio(clienteJson.optString("phone"), "Não informado"), "Email: " + valorOuVazio(clienteJson.optString("email"), "Não informado"), Color.rgb(239, 246, 255)));
        raiz.addView(cardLeitura("Endereço", valorOuVazio(clienteJson.optString("address"), "Não informado"), "Cidade: " + valorOuVazio(clienteJson.optString("city"), "Não informada"), "Observação: " + valorOuVazio(clienteJson.optString("notes"), "Sem observações"), Color.rgb(248, 250, 252)));
        TextView resumo = texto("Carregando histórico...", 15, true);
        raiz.addView(resumo);
        LinearLayout lista = coluna();
        raiz.addView(lista);
        Button voltar = botao("Voltar para Clientes", Color.rgb(30, 64, 175));
        voltar.setOnClickListener(v -> abrirModuloClientes(""));
        raiz.addView(voltar);
        Button home = botao("Voltar para Home", Color.rgb(37, 99, 235));
        home.setOnClickListener(v -> mostrarHomeModulos());
        raiz.addView(home);
        setContentView(scroll);
        carregarDetalheCliente(clienteJson.optString("id"), resumo, lista);
    }

    private void carregarDetalheCliente(String id, TextView resumo, LinearLayout lista) {
        new Thread(() -> {
            try {
                JSONObject stats = buscarObjetoApi("/api/clients/" + URLEncoder.encode(id, "UTF-8") + "/stats");
                JSONObject s = stats.optJSONObject("stats");
                JSONArray produtosTop = stats.optJSONArray("by_product");
                runOnUiThread(() -> {
                    lista.removeAllViews();
                    resumo.setText("Histórico resumido");
                    if (s != null) {
                        lista.addView(cardLeitura("Compras", "Total: " + moeda.format(s.optDouble("total_value", 0)), "Registros: " + s.optInt("total_sales", 0), "Ticket médio: " + moeda.format(s.optDouble("avg_ticket", 0)), Color.rgb(240, 253, 244)));
                    }
                    if (produtosTop != null && produtosTop.length() > 0) {
                        for (int i = 0; i < Math.min(3, produtosTop.length()); i++) {
                            JSONObject p = produtosTop.optJSONObject(i);
                            if (p != null) lista.addView(cardLeitura(p.optString("product", "Produto"), "Total: " + moeda.format(p.optDouble("val", 0)), "Qtd: " + formatarNumero(p.optDouble("qty", 0)), "", Color.rgb(248, 250, 252)));
                        }
                    }
                });
            } catch (Exception e) {
                runOnUiThread(() -> {
                    resumo.setText("Histórico indisponível no momento.");
                    lista.addView(texto(e.getMessage(), 13, false));
                });
            }
        }).start();
    }

    private void abrirModuloConsolidado(String periodo) {
        temaEscuroAtivo = true;
        telaAtual = "consolidado";
        ScrollView scroll = new ScrollView(this);
        scroll.setBackgroundColor(COR_FUNDO_ESCURO);
        LinearLayout raiz = coluna();
        raiz.setBackgroundColor(COR_FUNDO_ESCURO);
        raiz.setPadding(dp(18), dp(18), dp(18), dp(28));
        scroll.addView(raiz);
        adicionarCabecalhoModulo(raiz, "Consolidado", "Resumo por período para leitura rápida.");
        adicionarBannerModulo(raiz, "VISÃO GERAL", "Entenda o resultado do período", "Vendas, avarias e saldo líquido organizados em uma leitura única.", Color.rgb(124, 58, 237));
        adicionarFiltrosPeriodo(raiz, periodo, p -> abrirModuloConsolidado(p));
        TextView resumo = texto("Carregando consolidado...", 15, true);
        raiz.addView(resumo);
        LinearLayout lista = coluna();
        raiz.addView(lista);
        Button atualizar = botao("↻ Atualizar", Color.rgb(21, 101, 52));
        atualizar.setTextSize(13);
        atualizar.setOnClickListener(v -> carregarConsolidado(periodo, resumo, lista, atualizar));
        raiz.addView(atualizar);
        setContentView(scroll);
        carregarConsolidado(periodo, resumo, lista, atualizar);
    }

    private void carregarConsolidado(String periodo, TextView resumo, LinearLayout lista, Button atualizar) {
        lista.removeAllViews();
        resumo.setText("Carregando consolidado...");
        atualizar.setEnabled(false);
        new Thread(() -> {
            try {
                JSONArray rows = buscarSalesApi("", anoPeriodo(periodo), mesPeriodo(periodo), 1000);
                double receita = 0, avarias = 0;
                int entregas = 0, registros = 0;
                LinkedHashMap<String, double[]> porDia = new LinkedHashMap<>();
                for (int i = 0; i < rows.length(); i++) {
                    JSONObject r = rows.getJSONObject(i);
                    if (!dentroDoPeriodo(r.optString("sale_date"), periodo)) continue;
                    String tipo = r.optString("sale_type", "");
                    double valor = r.optDouble("total", 0);
                    registros++;
                    if ("AVARIA".equalsIgnoreCase(tipo)) {
                        avarias += Math.abs(valor);
                    } else {
                        receita += valor;
                        entregas++;
                        String dia = r.optString("sale_date", "Sem data");
                        double[] acc = porDia.containsKey(dia) ? porDia.get(dia) : new double[]{0, 0};
                        acc[0] += valor;
                        acc[1] += 1;
                        porDia.put(dia, acc);
                    }
                }
                double receitaFinal = receita, avariasFinal = avarias;
                int entregasFinal = entregas, registrosFinal = registros;
                runOnUiThread(() -> {
                    lista.removeAllViews();
                    resumo.setText(nomePeriodo(periodo) + " • " + registrosFinal + " registro(s)");
                    lista.addView(cardResultadoLiquido(receitaFinal - avariasFinal));
                    lista.addView(linhaKpis(
                        cardIndicador("Vendas", moeda.format(receitaFinal), entregasFinal + " nota(s)/entrega(s)", Color.rgb(52, 190, 145)),
                        cardIndicador("Avarias", moeda.format(avariasFinal), "Valor no período", Color.rgb(239, 105, 91))));
                    lista.addView(linhaKpis(
                        cardIndicador("Ticket médio", moeda.format(entregasFinal > 0 ? receitaFinal / entregasFinal : 0), "Por nota/entrega", Color.rgb(96, 165, 250)),
                        cardIndicador("Movimentações", String.valueOf(registrosFinal), "Vendas + avarias", Color.rgb(168, 139, 250))));
                    if (!porDia.isEmpty()) {
                        lista.addView(graficoLinhaAnimado("Vendas por dia", rotulosGraficoDia(porDia, 12), valoresGraficoDia(porDia, 12), Color.rgb(52, 190, 145), 0));
                        double maximo = Math.max(receitaFinal, avariasFinal);
                        lista.addView(graficoBarra("Impacto financeiro das avarias", avariasFinal, maximo, Color.rgb(239, 105, 91)));
                    } else {
                        lista.addView(texto("Sem vendas registradas neste período.", 14, false));
                    }
                    atualizar.setEnabled(true);
                });
            } catch (Exception e) {
                runOnUiThread(() -> {
                    lista.removeAllViews();
                    resumo.setText("Não foi possível carregar.");
                    lista.addView(cardLeitura("Consolidado indisponível", "Não foi possível atualizar os registros.", "Confira a conexão e tente novamente.", e.getMessage(), Color.rgb(255, 247, 237)));
                    atualizar.setEnabled(true);
                });
            }
        }).start();
    }

    private interface AcaoPeriodo { void executar(String periodo); }

    private void adicionarFiltrosPeriodo(LinearLayout raiz, String periodo, AcaoPeriodo acao) {
        LinearLayout linha1 = new LinearLayout(this);
        linha1.setOrientation(LinearLayout.HORIZONTAL);
        linha1.addView(botaoFiltro("Hoje", "hoje".equals(periodo), () -> acao.executar("hoje")), paramsFiltro(0));
        linha1.addView(botaoFiltro("Semana", "semana".equals(periodo), () -> acao.executar("semana")), paramsFiltro(1));
        raiz.addView(linha1);
        LinearLayout linha2 = new LinearLayout(this);
        linha2.setOrientation(LinearLayout.HORIZONTAL);
        linha2.addView(botaoFiltro("Mês atual", "mes".equals(periodo), () -> acao.executar("mes")), paramsFiltro(0));
        linha2.addView(botaoFiltro("Mês anterior", "mes_anterior".equals(periodo), () -> acao.executar("mes_anterior")), paramsFiltro(1));
        raiz.addView(linha2);
    }

    private Button botaoFiltro(String texto, boolean ativo, Runnable acao) {
        Button b = botao(texto, ativo ? Color.rgb(21, 101, 52) : Color.WHITE);
        b.setTextSize(13);
        b.setTextColor(ativo ? Color.WHITE : Color.rgb(39, 57, 45));
        b.setBackground(fundoComBorda(ativo ? Color.rgb(21, 101, 52) : Color.WHITE, ativo ? Color.rgb(21, 101, 52) : Color.rgb(216, 227, 220), 10));
        b.setOnClickListener(v -> acao.run());
        return b;
    }

    private LinearLayout.LayoutParams paramsFiltro(int posicao) {
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(0, dp(48), 1);
        p.setMargins(posicao == 0 ? 0 : dp(4), dp(5), dp(4), dp(5));
        return p;
    }

    private View cardLeitura(String titulo, String linha1, String linha2, String linha3, int cor) {
        LinearLayout card = coluna();
        card.setPadding(dp(12), dp(10), dp(12), dp(10));
        card.setBackground(temaEscuroAtivo ? fundoCardEscuro(cor) : fundoArredondado(cor, 12));
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-1, -2);
        params.setMargins(0, dp(6), 0, dp(6));
        card.setLayoutParams(params);
        card.addView(texto(titulo == null || titulo.trim().isEmpty() ? "Sem título" : titulo, 17, true));
        if (linha1 != null && !linha1.trim().isEmpty()) card.addView(texto(linha1, 14, false));
        if (linha2 != null && !linha2.trim().isEmpty()) card.addView(texto(linha2, 14, false));
        if (linha3 != null && !linha3.trim().isEmpty()) card.addView(texto(linha3, 13, false));
        card.setElevation(dp(3));
        aplicarFeedbackToque(card);
        return card;
    }

    private void abrirPainelAnalises(String periodo) {
        temaEscuroAtivo = true; telaAtual = "analises";
        ScrollView scroll = new ScrollView(this); scroll.setBackgroundColor(COR_FUNDO_ESCURO);
        LinearLayout raiz = coluna(); raiz.setPadding(dp(16), dp(14), dp(16), dp(24)); scroll.addView(raiz);
        adicionarCabecalhoModulo(raiz, "Análises", "Indicadores atuais de vendas, avarias e operação.");
        TextView filtrosAtivos = texto("⌕  Filtros   Todas as lojas · Todos os produtos", 13, true);
        filtrosAtivos.setPadding(dp(12), dp(12), dp(12), dp(12));
        filtrosAtivos.setBackground(fundoComBorda(Color.WHITE, Color.rgb(216, 227, 220), 18));
        raiz.addView(filtrosAtivos);
        LinearLayout filtros = new LinearLayout(this); filtros.setOrientation(LinearLayout.HORIZONTAL);
        for (String[] f : new String[][]{{"Hoje","hoje"},{"7 dias","semana"},{"Mês","mes"}}) {
            Button b = botaoFiltro(f[0], f[1].equals(periodo), () -> abrirPainelAnalises(f[1])); filtros.addView(b, paramsFiltro(filtros.getChildCount()));
        }
        raiz.addView(filtros);
        TextView status = texto("Atualizando indicadores do ERP…", 13, false); raiz.addView(status);
        LinearLayout cards = coluna(); raiz.addView(cards);
        LinearLayout atalhos = coluna(); raiz.addView(atalhos);
        atalhos.addView(botaoModulo("Avarias", "Ver ocorrências e lançar uma avaria", Color.rgb(185, 55, 45), () -> abrirModuloAvarias("mes")));
        atalhos.addView(botaoModulo("Produtividade", "Produção e dias ativos", Color.rgb(22, 163, 74), () -> abrirModuloProdutividade("mes")));
        atalhos.addView(botaoModulo("Projeção", "Estimativa de saída", Color.rgb(59, 130, 246), () -> abrirModuloProjecao("30", "", "", "consolidada")));
        setContentView(scroll);
        new Thread(() -> {
            try {
                Calendar c = Calendar.getInstance(); JSONArray rows = buscarSalesApi("", c.get(Calendar.YEAR), c.get(Calendar.MONTH) + 1, 1000);
                if ("semana".equals(periodo)) { Calendar anterior=(Calendar)c.clone();anterior.add(Calendar.MONTH,-1);JSONArray velhas=buscarSalesApi("",anterior.get(Calendar.YEAR),anterior.get(Calendar.MONTH)+1,1000);for(int i=0;i<velhas.length();i++)rows.put(velhas.optJSONObject(i)); }
                double vendas=0, avarias=0; int notas=0; LinkedHashMap<String,double[]> dias=new LinkedHashMap<>(); LinkedHashMap<String,Double> produtos=new LinkedHashMap<>();
                for (int i=0;i<rows.length();i++) { JSONObject r=rows.optJSONObject(i); if(r==null || !dentroDoPeriodo(r.optString("sale_date"), periodo)) continue;
                    double valor=r.optDouble("total",0); String tipo=r.optString("sale_type","");
                    if("AVARIA".equalsIgnoreCase(tipo)){avarias+=valor;continue;} vendas+=valor; notas++;
                    String data=r.optString("sale_date","—"); double[] acc=dias.containsKey(data)?dias.get(data):new double[]{0}; acc[0]+=valor; dias.put(data,acc);
                    String prod=r.optString("product","Produto"); produtos.put(prod, (produtos.containsKey(prod)?produtos.get(prod):0)+valor);
                }
                double v=vendas,a=avarias; int n=notas;
                runOnUiThread(() -> { status.setText(nomePeriodo(periodo)+" · "+n+" notas e "+formatarNumero(dias.size())+" dias com movimento"); cards.removeAllViews();
                    cards.addView(linhaKpis(cardIndicador("Vendas", moeda.format(v), n+" notas", Color.rgb(21,101,52)),cardIndicador("Avarias",moeda.format(a),"Valor registrado",Color.rgb(220,38,38))));
                    cards.addView(linhaKpis(cardIndicador("Ticket médio",moeda.format(n>0?v/n:0),"Por nota",Color.rgb(37,99,235)),cardIndicador("Dias ativos",String.valueOf(dias.size()),"No período",Color.rgb(13,148,136))));
                    if(!dias.isEmpty()) cards.addView(graficoLinhaAnimado("Evolução de vendas",rotulosGraficoDia(dias,7),valoresGraficoDia(dias,7),Color.rgb(21,128,61),0));
                    List<Map.Entry<String,Double>> top=new ArrayList<>(produtos.entrySet()); Collections.sort(top,(x,y)->Double.compare(y.getValue(),x.getValue()));
                    cards.addView(texto("Top produtos · mais vendidos no período",16,true));
                    for(int i=0;i<Math.min(3,top.size());i++){Map.Entry<String,Double> e=top.get(i);double share=v>0?e.getValue()*100d/v:0;cards.addView(linhaResumoMobile((i+1)+"  "+e.getKey(),String.format(Locale.forLanguageTag("pt-BR"),"%.1f%% das vendas",share),moeda.format(e.getValue()),Color.rgb(21,101,52)));}
                });
            } catch(Exception e){runOnUiThread(()->status.setText("Falha ao atualizar análises: "+mensagemErroSimples(e)));}
        }).start();
    }

    private void abrirSincronizacaoERP() {
        temaEscuroAtivo=true; telaAtual="sincronizacao_erp"; ScrollView scroll=new ScrollView(this); scroll.setBackgroundColor(COR_FUNDO_ESCURO);
        LinearLayout raiz=coluna(); raiz.setPadding(dp(16),dp(14),dp(16),dp(24)); scroll.addView(raiz);
        adicionarCabecalhoModulo(raiz,"Sincronização com ERP","Acompanhe a consulta do aplicativo ao sistema.");
        TextView status=texto("◷  Conectando ao ERP…",16,true); status.setPadding(dp(14),dp(14),dp(14),dp(14)); status.setBackground(fundoComBorda(Color.rgb(240,248,242),Color.rgb(205,225,209),12)); raiz.addView(status);
        LinearLayout resumo=coluna(); raiz.addView(resumo);
        TextView tituloLista=texto("Últimas notas consultadas",17,true);tituloLista.setPadding(0,dp(14),0,dp(5));raiz.addView(tituloLista);
        LinearLayout lista=coluna(); raiz.addView(lista); Button atualizar=botao("⟳  Sincronizar agora",Color.rgb(21,101,52)); raiz.addView(atualizar);
        Runnable carregar=()->{atualizar.setEnabled(false);status.setText("Consultando o ERP…");new Thread(()->{try{
            JSONArray dados=buscarArrayApi("/api/sales/delivery-sync"); int entregues=0,pendentes=0; for(int i=0;i<dados.length();i++){JSONObject r=dados.optJSONObject(i);if(r!=null){if(!r.isNull("delivered")&& !r.optString("delivered").trim().isEmpty()) entregues++;else pendentes++;}}
            int ok=entregues, fila=pendentes; runOnUiThread(()->{String hora=new SimpleDateFormat("HH:mm",Locale.getDefault()).format(new java.util.Date());status.setText("✓  Conectado ao ERP\nÚltima sincronização: hoje, "+hora);resumo.removeAllViews();resumo.addView(linhaKpis(cardIndicador("Consultadas",String.valueOf(dados.length()),"Notas lidas",Color.rgb(21,101,52)),cardIndicador("Confirmadas",String.valueOf(ok),"Status de entrega",Color.rgb(37,99,235))));resumo.addView(cardIndicador("Aguardando confirmação",String.valueOf(fila),"O ERP ainda não marcou como entregue",Color.rgb(202,138,4)));lista.removeAllViews();int exibidas=0;for(int i=0;i<dados.length()&&exibidas<8;i++){JSONObject r=dados.optJSONObject(i);if(r==null)continue;boolean confirmada=!r.isNull("delivered")&&!r.optString("delivered").trim().isEmpty();String id=r.optString("id","—");String data=r.optString("delivered_at","");lista.addView(cardLeitura("Entrega #"+id,confirmada?"Gravado no ERP":"Aguardando confirmação do ERP",data.isEmpty()?"Consulta concluída":"Confirmada em "+data, "",confirmada?Color.rgb(220,252,231):Color.rgb(255,247,237)));exibidas++;}if(exibidas==0)lista.addView(cardLeitura("Sem registros","A consulta foi concluída sem notas nesta lista.","Quando houver registros, o status aparecerá aqui.","",Color.rgb(240,248,242)));lista.addView(cardLeitura("Consulta somente de leitura","Não houve envio ou reenvio de vendas.","O status exibido é o que a API do ERP disponibiliza.","",Color.rgb(239,246,255)));atualizar.setEnabled(true);});
        }catch(Exception e){runOnUiThread(()->{status.setText("Não foi possível sincronizar: "+mensagemErroSimples(e));atualizar.setEnabled(true);});}}).start();}; atualizar.setOnClickListener(v->carregar.run());setContentView(scroll);carregar.run();
    }

    private void abrirSeletorRelatorioDebitos() {
        if (!"admin".equalsIgnoreCase(authPrefs().getString("role", "").trim())) { aviso("Relatório disponível somente para administradores."); return; }
        new Thread(() -> { try { JSONArray clientes=buscarArrayApi("/api/boletos/debtor-report/clients?scope=open"); runOnUiThread(()->mostrarSeletorRelatorioDebitos(clientes)); }
            catch(Exception e){runOnUiThread(()->aviso("Não foi possível carregar clientes devedores: "+mensagemErroSimples(e)));} }).start();
    }

    private void mostrarSeletorRelatorioDebitos(JSONArray clientes) {
        LinearLayout form=coluna(); form.setPadding(dp(16),dp(8),dp(16),dp(8));
        Spinner escopo=new Spinner(this); escopo.setAdapter(adaptadorSpinner(new String[]{"Todos em aberto","Somente em atraso","Vencem hoje"}));
        Spinner cliente=new Spinner(this); CheckBox raios=new CheckBox(this), estrada=new CheckBox(this); raios.setText("Menina dos Raios"); estrada.setText("Menina da Estrada"); raios.setChecked(true);estrada.setChecked(true);
        TextView preview=texto("Selecione o cliente para ver o total.",14,false);
        form.addView(rotuloCampo("PERÍODO"));form.addView(escopo);form.addView(rotuloCampo("CLIENTE OU REDE (FILIAIS AGRUPADAS)"));form.addView(cliente);form.addView(rotuloCampo("EMPRESAS NO RELATÓRIO"));form.addView(raios);form.addView(estrada);form.addView(preview);
        JSONArray[] dados={clientes}; ArrayList<String> nomes=new ArrayList<>(); ArrayList<String> chaves=new ArrayList<>();
        for(int i=0;i<clientes.length();i++){JSONObject c=clientes.optJSONObject(i);if(c!=null){nomes.add(c.optString("name"));chaves.add(c.optString("key"));}}
        cliente.setAdapter(new ArrayAdapter<String>(this,android.R.layout.simple_spinner_dropdown_item,nomes));
        AdapterView.OnItemSelectedListener atualiza=new AdapterView.OnItemSelectedListener(){public void onNothingSelected(AdapterView<?> p){} public void onItemSelected(AdapterView<?> p,View v,int pos,long id){if(pos>=0&&pos<dados[0].length()){JSONObject c=dados[0].optJSONObject(pos);if(c!=null)preview.setText(c.optInt("invoice_count")+" nota(s) · saldo devedor "+moeda.format(c.optDouble("balance",0))+" · filiais agrupadas");}}}; cliente.setOnItemSelectedListener(atualiza);
        escopo.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener(){public void onNothingSelected(AdapterView<?> p){}public void onItemSelected(AdapterView<?> p,View v,int pos,long id){String s=pos==1?"overdue":(pos==2?"today":"open");new Thread(()->{try{JSONArray novos=buscarArrayApi("/api/boletos/debtor-report/clients?scope="+s);runOnUiThread(()->{dados[0]=novos;nomes.clear();chaves.clear();for(int i=0;i<novos.length();i++){JSONObject c=novos.optJSONObject(i);if(c!=null){nomes.add(c.optString("name"));chaves.add(c.optString("key"));}}((ArrayAdapter<?>)cliente.getAdapter()).notifyDataSetChanged();if(!nomes.isEmpty())cliente.setSelection(0);else preview.setText("Nenhum devedor neste filtro.");});}catch(Exception e){runOnUiThread(()->preview.setText("Falha ao filtrar clientes: "+mensagemErroSimples(e)));}}).start();}});
        AlertDialog dialog=new AlertDialog.Builder(this).setTitle("Relatório de débitos · PDF A4").setView(form).setNegativeButton("Cancelar",null).setPositiveButton("Gerar PDF",null).create();
        dialog.setOnShowListener(x->dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v->{int pos=cliente.getSelectedItemPosition();if(pos<0||pos>=chaves.size()){aviso("Selecione um cliente com saldo em aberto.");return;}if(!raios.isChecked()&&!estrada.isChecked()){aviso("Selecione ao menos uma empresa.");return;}String scope=escopo.getSelectedItemPosition()==1?"overdue":(escopo.getSelectedItemPosition()==2?"today":"open");String companies=(raios.isChecked()?"raios":"")+(raios.isChecked()&&estrada.isChecked()?",":"")+(estrada.isChecked()?"estrada":"");String endpoint="/api/boletos/debtor-report?client="+url(chaves.get(pos))+"&companies="+url(companies)+"&scope="+scope;v.setEnabled(false);new Thread(()->{try{JSONObject report=buscarObjetoApi(endpoint);File pdf=criarPdfRelatorioDebitos(report);runOnUiThread(()->{dialog.dismiss();compartilharPdf(pdf);});}catch(Exception e){runOnUiThread(()->{v.setEnabled(true);aviso("Não foi possível gerar o relatório: "+mensagemErroSimples(e));});}}).start();}));dialog.show();
    }

    private String url(String valor) { try{return URLEncoder.encode(valor,"UTF-8");}catch(Exception e){return valor;} }

    private File criarPdfRelatorioDebitos(JSONObject report) throws Exception {
        PdfDocument pdf=new PdfDocument(); PdfDocument.PageInfo info=new PdfDocument.PageInfo.Builder(595,842,1).create(); PdfDocument.Page page=pdf.startPage(info); android.graphics.Canvas c=page.getCanvas();
        JSONArray invoices=report.optJSONArray("invoices");if(invoices==null)invoices=new JSONArray();JSONArray totals=report.optJSONArray("company_totals");if(totals==null)totals=new JSONArray();
        float scale=Math.min(1f,790f/(210f+invoices.length()*13f)); c.save();c.scale(scale,scale);float w=595/scale;int y=36;Paint p=new Paint(3);p.setColor(Color.rgb(20,83,45));p.setTypeface(android.graphics.Typeface.create("sans-serif",1));p.setTextSize(20);c.drawText("RELATÓRIO DE DÉBITOS",28,y,p);y+=23;
        p.setColor(Color.DKGRAY);p.setTextSize(11);p.setTypeface(android.graphics.Typeface.DEFAULT);c.drawText("Cliente / rede: "+report.optString("client"),28,y,p);y+=16;c.drawText("Emitido em "+new SimpleDateFormat("dd/MM/yyyy",new Locale("pt","BR")).format(new java.util.Date())+" · notas em aberto",28,y,p);y+=20;
        for(int i=0;i<totals.length();i++){JSONObject t=totals.optJSONObject(i);if(t==null)continue;p.setColor(i%2==0?Color.rgb(220,252,231):Color.rgb(219,234,254));c.drawRect(28,y-12,w-28,y+7,p);p.setColor(Color.rgb(20,83,45));p.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);p.setTextSize(11);c.drawText(t.optString("name")+" · "+t.optInt("invoice_count")+" NF(s)",34,y,p);String subtotal=moeda.format(t.optDouble("total",0));p.setTextAlign(Paint.Align.RIGHT);c.drawText(subtotal,w-34,y,p);p.setTextAlign(Paint.Align.LEFT);y+=19;}
        p.setColor(Color.GRAY);p.setTextSize(8);p.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);c.drawText("EMPRESA / FILIAL · NF",30,y,p);c.drawText("VENCIMENTO",330,y,p);p.setTextAlign(Paint.Align.RIGHT);c.drawText("SALDO",w-30,y,p);p.setTextAlign(Paint.Align.LEFT);y+=12;
        for(int i=0;i<invoices.length();i++){JSONObject row=invoices.optJSONObject(i);if(row==null)continue;p.setColor(i%2==0?Color.rgb(248,250,248):Color.WHITE);c.drawRect(28,y-9,w-28,y+5,p);p.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);p.setTextSize(8);p.setColor(Color.rgb(31,41,55));String line=row.optString("company")+" · "+row.optString("client")+" · NF "+row.optString("nf_number","—");c.drawText(line,30,y,p);p.setTypeface(android.graphics.Typeface.DEFAULT);c.drawText(formatarDataIso(row.optString("due_date","")),330,y,p);p.setTextAlign(Paint.Align.RIGHT);c.drawText(moeda.format(row.optDouble("balance",0)),w-30,y,p);p.setTextAlign(Paint.Align.LEFT);y+=13;}
        p.setColor(Color.rgb(20,83,45));c.drawRect(28,y,w-28,y+24,p);p.setColor(Color.WHITE);p.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);p.setTextSize(13);c.drawText("TOTAL GERAL · "+report.optInt("invoice_count")+" notas",36,y+16,p);p.setTextAlign(Paint.Align.RIGHT);c.drawText(moeda.format(report.optDouble("total",0)),w-36,y+16,p);p.setTextAlign(Paint.Align.LEFT);c.restore();pdf.finishPage(page);
        File dir=new File(getCacheDir(),"pedidos");if(!dir.exists()&&!dir.mkdirs())throw new Exception("Não foi possível preparar o PDF.");File file=new File(dir,"relatorio_debitos_"+System.currentTimeMillis()+".pdf");java.io.FileOutputStream out=new java.io.FileOutputStream(file);pdf.writeTo(out);out.close();pdf.close();return file;
    }

    private void compartilharPdf(File file) {
        Uri uri=Uri.parse("content://"+getPackageName()+".files/pedidos/"+file.getName());Intent send=new Intent(Intent.ACTION_SEND);send.setType("application/pdf");send.putExtra(Intent.EXTRA_STREAM,uri);send.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        try{startActivity(Intent.createChooser(send,"Enviar relatório de débitos"));}catch(Exception e){aviso("PDF criado, mas não foi possível abrir o compartilhamento.");}
    }

    private View graficoBarra(String titulo, double valor, double maximo, int cor) {
        LinearLayout card = coluna();
        card.setPadding(dp(12), dp(10), dp(12), dp(10));
        card.setBackground(fundoCardEscuro(cor));
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-1, -2);
        params.setMargins(0, dp(5), 0, dp(5));
        card.setLayoutParams(params);
        card.addView(texto(titulo, 14, true));
        LinearLayout trilho = new LinearLayout(this);
        trilho.setOrientation(LinearLayout.HORIZONTAL);
        trilho.setBackground(fundoArredondado(Color.rgb(226, 234, 228), 8));
        LinearLayout.LayoutParams trilhoParams = new LinearLayout.LayoutParams(-1, dp(12));
        trilhoParams.setMargins(0, dp(7), 0, dp(5));
        int peso = maximo <= 0 ? 0 : Math.max(1, Math.min(100, (int)Math.round((valor / maximo) * 100)));
        View preenchido = new View(this);
        preenchido.setBackground(fundoArredondado(cor, 8));
        trilho.addView(preenchido, new LinearLayout.LayoutParams(0, dp(12), peso));
        View vazio = new View(this);
        trilho.addView(vazio, new LinearLayout.LayoutParams(0, dp(12), Math.max(1, 100 - peso)));
        card.addView(trilho, trilhoParams);
        TextView v = texto(formatarNumero(valor), 13, false);
        v.setTextColor(COR_TEXTO_SUAVE);
        card.addView(v);
        preenchido.setPivotX(0);
        preenchido.setScaleX(0f);
        preenchido.postDelayed(() -> preenchido.animate().scaleX(1f).setDuration(850).start(), 120);
        return card;
    }

    private View graficoMeta(String titulo, double realizado, double meta, int cor) {
        double perc = meta <= 0 ? 0 : (realizado / meta) * 100;
        int corEstado = corEstadoMeta(perc);
        String status = textoEstadoMeta(perc);
        LinearLayout card = coluna();
        card.setPadding(dp(14), dp(12), dp(14), dp(12));
        card.setBackground(fundoCardEscuro(corEstado));
        card.addView(texto(titulo, 17, true));
        card.addView(texto(status + " - " + formatarNumero(perc) + "%", 14, false));
        card.addView(graficoBarra("Realizado: " + formatarNumero(realizado) + " / Meta: " + formatarNumero(meta), Math.min(realizado, meta), meta, corEstado));
        return card;
    }

    private View graficoBarrasAnimado(String titulo, List<String> rotulos, List<Double> valores, int cor, double meta) {
        if (rotulos == null || valores == null || valores.isEmpty()) return cardLeitura(titulo, "Sem dados para exibir.", "", "", Color.rgb(148, 163, 184));
        BarChart chart = new BarChart(this);
        chart.setLayoutParams(new LinearLayout.LayoutParams(-1, dp(230)));
        ArrayList<BarEntry> entradas = new ArrayList<>();
        for (int i = 0; i < valores.size(); i++) entradas.add(new BarEntry(i, (float)Math.max(0, valores.get(i))));
        BarDataSet set = new BarDataSet(entradas, titulo);
        set.setColor(cor);
        set.setHighLightColor(Color.WHITE);
        set.setValueTextColor(COR_TEXTO_CLARO);
        set.setValueTextSize(9f);
        set.setDrawValues(valores.size() <= 8);
        BarData data = new BarData(set);
        data.setBarWidth(0.56f);
        chart.setData(data);
        configurarGraficoEscuro(chart, rotulos, meta, cor);
        chart.animateY(850);
        chart.invalidate();
        return cardGrafico(titulo, chart);
    }

    private View graficoLinhaAnimado(String titulo, List<String> rotulos, List<Double> valores, int cor, double meta) {
        if (rotulos == null || valores == null || valores.isEmpty()) return cardLeitura(titulo, "Sem dados para exibir.", "", "", Color.rgb(148, 163, 184));
        LineChart chart = new LineChart(this);
        chart.setLayoutParams(new LinearLayout.LayoutParams(-1, dp(230)));
        ArrayList<Entry> entradas = new ArrayList<>();
        for (int i = 0; i < valores.size(); i++) entradas.add(new Entry(i, (float)Math.max(0, valores.get(i))));
        LineDataSet set = new LineDataSet(entradas, titulo);
        set.setColor(cor);
        set.setCircleColor(cor);
        set.setCircleRadius(3.5f);
        set.setLineWidth(2.4f);
        set.setMode(LineDataSet.Mode.CUBIC_BEZIER);
        set.setDrawFilled(true);
        set.setFillColor(cor);
        set.setFillAlpha(70);
        set.setValueTextColor(COR_TEXTO_CLARO);
        set.setValueTextSize(9f);
        set.setDrawValues(valores.size() <= 8);
        LineData data = new LineData(set);
        chart.setData(data);
        configurarGraficoEscuro(chart, rotulos, meta, cor);
        chart.animateXY(850, 850);
        chart.invalidate();
        return cardGrafico(titulo, chart);
    }

    private View cardGrafico(String titulo, View chart) {
        LinearLayout card = coluna();
        card.setPadding(dp(12), dp(12), dp(12), dp(10));
        card.setBackground(fundoCardEscuro(Color.rgb(59, 130, 246)));
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-1, -2);
        params.setMargins(0, dp(7), 0, dp(7));
        card.setLayoutParams(params);
        card.addView(texto(titulo, 17, true));
        card.addView(chart);
        card.setElevation(dp(4));
        aplicarFeedbackToque(card);
        return card;
    }

    private void configurarGraficoEscuro(com.github.mikephil.charting.charts.Chart<?> chart, List<String> rotulos, double meta, int cor) {
        chart.setBackgroundColor(Color.TRANSPARENT);
        chart.getDescription().setEnabled(false);
        chart.setNoDataText("Sem dados");
        chart.setNoDataTextColor(COR_TEXTO_SUAVE);
        Legend legenda = chart.getLegend();
        legenda.setTextColor(COR_TEXTO_SUAVE);
        legenda.setTextSize(10f);
        if (chart instanceof BarChart) {
            BarChart bar = (BarChart) chart;
            configurarEixos(bar.getXAxis(), bar.getAxisLeft(), bar.getAxisRight(), rotulos, meta, cor);
            bar.setFitBars(true);
            bar.setScaleEnabled(false);
        } else if (chart instanceof LineChart) {
            LineChart line = (LineChart) chart;
            configurarEixos(line.getXAxis(), line.getAxisLeft(), line.getAxisRight(), rotulos, meta, cor);
            line.setScaleEnabled(false);
        }
    }

    private void configurarEixos(XAxis x, YAxis esquerda, YAxis direita, List<String> rotulos, double meta, int cor) {
        x.setPosition(XAxis.XAxisPosition.BOTTOM);
        x.setTextColor(COR_TEXTO_SUAVE);
        x.setTextSize(9f);
        x.setDrawGridLines(false);
        x.setGranularity(1f);
        x.setLabelCount(Math.min(rotulos.size(), 6), false);
        x.setValueFormatter(new ValueFormatter() {
            @Override public String getAxisLabel(float value, AxisBase axis) {
                int idx = Math.round(value);
                return idx >= 0 && idx < rotulos.size() ? rotulos.get(idx) : "";
            }
        });
        esquerda.setTextColor(COR_TEXTO_SUAVE);
        esquerda.setGridColor(Color.rgb(226, 234, 228));
        esquerda.setAxisLineColor(Color.rgb(203, 213, 225));
        esquerda.setAxisMinimum(0f);
        esquerda.removeAllLimitLines();
        if (meta > 0) {
            LimitLine linhaMeta = new LimitLine((float) meta, "Meta");
            linhaMeta.setLineColor(corEstadoMeta(100));
            linhaMeta.setTextColor(COR_TEXTO_CLARO);
            linhaMeta.setTextSize(10f);
            linhaMeta.setLineWidth(1.4f);
            esquerda.addLimitLine(linhaMeta);
        }
        direita.setEnabled(false);
    }

    private String textoEstadoMeta(double perc) {
        if (perc >= 100) return "Acima da meta";
        if (perc >= 80) return "Dentro da meta";
        return "Abaixo da meta";
    }

    private int corEstadoMeta(double perc) {
        if (perc >= 100) return Color.rgb(34, 197, 94);
        if (perc >= 80) return Color.rgb(245, 158, 11);
        return Color.rgb(239, 68, 68);
    }

    private List<String> rotulosGraficoDia(LinkedHashMap<String, double[]> mapa, int limite) {
        List<String> todos = new ArrayList<>(mapa.keySet());
        int inicio = Math.max(0, todos.size() - limite);
        List<String> rotulos = new ArrayList<>();
        for (int i = inicio; i < todos.size(); i++) rotulos.add(dataCurta(todos.get(i)));
        return rotulos;
    }

    private List<Double> valoresGraficoDia(LinkedHashMap<String, double[]> mapa, int limite) {
        List<String> todos = new ArrayList<>(mapa.keySet());
        int inicio = Math.max(0, todos.size() - limite);
        List<Double> valores = new ArrayList<>();
        for (int i = inicio; i < todos.size(); i++) valores.add(mapa.get(todos.get(i))[0]);
        return valores;
    }

    private List<String> rotulosTendencia(JSONArray arr, int limite) {
        List<String> rotulos = new ArrayList<>();
        if (arr == null) return rotulos;
        int inicio = Math.max(0, arr.length() - limite);
        for (int i = inicio; i < arr.length(); i++) {
            JSONObject o = arr.optJSONObject(i);
            rotulos.add(dataCurta(o == null ? "" : o.optString("data")));
        }
        return rotulos;
    }

    private List<Double> valoresTendencia(JSONArray arr, int limite) {
        List<Double> valores = new ArrayList<>();
        if (arr == null) return valores;
        int inicio = Math.max(0, arr.length() - limite);
        for (int i = inicio; i < arr.length(); i++) {
            JSONObject o = arr.optJSONObject(i);
            valores.add(o == null ? 0 : o.optDouble("total", 0));
        }
        return valores;
    }

    private String dataCurta(String data) {
        String br = dataBR(data);
        return br != null && br.length() >= 5 ? br.substring(0, 5) : br;
    }

    private JSONArray buscarSalesApi(String saleType, int year, int month, int limit) throws Exception {
        String endpoint = "/api/sales?year=" + year + "&month=" + month + "&limit=" + limit;
        if (saleType != null && !saleType.trim().isEmpty()) endpoint += "&sale_type=" + URLEncoder.encode(saleType, "UTF-8");
        return buscarArrayApi(endpoint);
    }

    private JSONArray buscarClientesApi(String busca) throws Exception {
        String endpoint = "/api/clients";
        if (busca != null && !busca.trim().isEmpty()) endpoint += "?search=" + URLEncoder.encode(busca.trim(), "UTF-8");
        return buscarArrayApi(endpoint);
    }

    private JSONArray buscarArrayApi(String endpoint) throws Exception {
        String json = buscarTextoApi(endpoint);
        return new JSONArray(json);
    }

    private JSONObject buscarObjetoApi(String endpoint) throws Exception {
        String json = buscarTextoApi(endpoint);
        String resposta = json == null ? "" : json.trim();
        if (resposta.startsWith("<")) {
            throw new Exception("O servidor ERP retornou uma página HTML em vez dos dados. A API está indisponível; tente novamente quando o serviço for restabelecido.");
        }
        try {
            return new JSONObject(resposta);
        } catch (org.json.JSONException e) {
            throw new Exception("O servidor ERP respondeu em um formato inválido. Nenhum dado foi carregado.");
        }
    }

    private String buscarTextoApi(String endpoint) throws Exception {
        HttpURLConnection conexao = null;
        try {
            conexao = (HttpURLConnection) new URL(SERVER_BASE_URL + endpoint).openConnection();
            conexao.setRequestMethod("GET");
            conexao.setConnectTimeout(10000);
            conexao.setReadTimeout(18000);
            conexao.setRequestProperty("x-token", tokenSistema());
            int status = conexao.getResponseCode();
            byte[] resposta = lerFluxo(status >= 200 && status < 300 ? conexao.getInputStream() : conexao.getErrorStream());
            String texto = new String(resposta, "UTF-8");
            if (status < 200 || status >= 300) throw new Exception(texto.isEmpty() ? "erro " + status : texto);
            return texto;
        } finally {
            if (conexao != null) conexao.disconnect();
        }
    }

    private JSONObject enviarObjetoApi(String endpoint, String metodo, JSONObject body) throws Exception {
        HttpURLConnection conexao = null;
        try {
            byte[] conteudo = body.toString().getBytes("UTF-8");
            conexao = (HttpURLConnection) new URL(SERVER_BASE_URL + endpoint).openConnection();
            conexao.setRequestMethod(metodo);
            conexao.setDoOutput(true);
            conexao.setConnectTimeout(10000);
            conexao.setReadTimeout(18000);
            conexao.setRequestProperty("x-token", tokenSistema());
            conexao.setRequestProperty("Content-Type", "application/json; charset=UTF-8");
            conexao.setRequestProperty("Accept", "application/json");
            conexao.setFixedLengthStreamingMode(conteudo.length);
            try (java.io.OutputStream saida = conexao.getOutputStream()) { saida.write(conteudo); }
            int status = conexao.getResponseCode();
            byte[] resposta = lerFluxo(status >= 200 && status < 300 ? conexao.getInputStream() : conexao.getErrorStream());
            String texto = new String(resposta, "UTF-8");
            if (status < 200 || status >= 300) throw new Exception(texto.isEmpty() ? "servidor respondeu " + status : texto);
            return texto.isEmpty() ? new JSONObject() : new JSONObject(texto);
        } finally {
            if (conexao != null) conexao.disconnect();
        }
    }

    private int anoPeriodo(String periodo) {
        Calendar c = Calendar.getInstance();
        if ("mes_anterior".equals(periodo)) c.add(Calendar.MONTH, -1);
        return c.get(Calendar.YEAR);
    }

    private int mesPeriodo(String periodo) {
        Calendar c = Calendar.getInstance();
        if ("mes_anterior".equals(periodo)) c.add(Calendar.MONTH, -1);
        return c.get(Calendar.MONTH) + 1;
    }

    private boolean dentroDoPeriodo(String iso, String periodo) {
        try {
            if (iso == null || iso.length() < 10) return false;
            Calendar data = Calendar.getInstance();
            data.setTime(new SimpleDateFormat("yyyy-MM-dd", Locale.US).parse(iso.substring(0, 10)));
            Calendar hoje = Calendar.getInstance();
            if ("hoje".equals(periodo)) {
                return data.get(Calendar.YEAR) == hoje.get(Calendar.YEAR)
                    && data.get(Calendar.DAY_OF_YEAR) == hoje.get(Calendar.DAY_OF_YEAR);
            }
            if ("semana".equals(periodo)) {
                Calendar inicio = Calendar.getInstance();
                inicio.add(Calendar.DAY_OF_YEAR, -6);
                return !data.before(inicio) && !data.after(hoje);
            }
            if ("mes_anterior".equals(periodo)) hoje.add(Calendar.MONTH, -1);
            return data.get(Calendar.YEAR) == hoje.get(Calendar.YEAR)
                && data.get(Calendar.MONTH) == hoje.get(Calendar.MONTH);
        } catch (Exception e) {
            return false;
        }
    }

    private String nomePeriodo(String periodo) {
        if ("hoje".equals(periodo)) return "Hoje";
        if ("semana".equals(periodo)) return "Últimos 7 dias";
        if ("mes_anterior".equals(periodo)) return "Mês anterior";
        return "Mês atual";
    }

    private String documentoCliente(JSONObject c) {
        String cnpj = c.optString("cnpj", "");
        String cpf = c.optString("cpf", "");
        if (!cnpj.trim().isEmpty()) return "CNPJ: " + cnpj;
        if (!cpf.trim().isEmpty()) return "CPF: " + cpf;
        return "Documento não informado";
    }

    private String valorOuVazio(String valor, String padrao) {
        return valor == null || valor.trim().isEmpty() ? padrao : valor;
    }

    @Override public void onBackPressed() {
        if ("home".equals(telaAtual) || "auth".equals(telaAtual)) {
            super.onBackPressed();
        } else if ("entrega_voz".equals(telaAtual)) {
            encerrarEntregaVoz(true);
        } else if ("vale".equals(telaAtual)) {
            confirmarSaidaVale();
        } else {
            mostrarHomeModulos();
        }
    }

    private void mostrarLoginSistema() {
        telaAtual = "auth";
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        LinearLayout raiz = coluna();
        raiz.setPadding(dp(24), dp(28), dp(24), dp(32));

        ImageView logo = new ImageView(this);
        logo.setImageResource(com.exemplo.vendaswhatsapp.R.drawable.logo);
        logo.setScaleType(ImageView.ScaleType.CENTER_CROP);
        LinearLayout.LayoutParams logoParams = new LinearLayout.LayoutParams(dp(128), dp(128));
        logoParams.gravity = Gravity.CENTER_HORIZONTAL;
        logoParams.setMargins(0, dp(4), 0, dp(8));
        raiz.addView(logo, logoParams);

        TextView titulo = texto("Entrar no sistema", 25, true);
        titulo.setGravity(Gravity.CENTER_HORIZONTAL);
        titulo.setTextColor(Color.rgb(20, 83, 45));
        raiz.addView(titulo);
        TextView subtitulo = texto("Use o mesmo usuário e senha do site Menina dos Raios.", 15, false);
        subtitulo.setGravity(Gravity.CENTER_HORIZONTAL);
        subtitulo.setPadding(0, 0, 0, dp(16));
        raiz.addView(subtitulo);

        EditText usuario = campo("Usuário", InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS);
        EditText senha = campo("Senha", InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD);
        raiz.addView(texto("Usuário", 13, false));
        raiz.addView(usuario);
        raiz.addView(texto("Senha", 13, false));
        raiz.addView(senha);

        Button entrar = botao("Entrar", Color.rgb(21, 128, 61));
        entrar.setOnClickListener(v -> realizarLoginSistema(usuario.getText().toString().trim(), senha.getText().toString(), entrar));
        raiz.addView(entrar);

        TextView rodape = texto("Sua sessao fica salva por token seguro. A senha nao e gravada no aparelho.", 13, false);
        rodape.setGravity(Gravity.CENTER_HORIZONTAL);
        rodape.setPadding(0, dp(10), 0, 0);
        raiz.addView(rodape);
        setContentView(montarTelaAutenticacao(scroll, raiz));
        usuario.requestFocus();
        usuario.postDelayed(() -> mostrarTeclado(usuario), 250);
    }

    private FrameLayout montarTelaAutenticacao(ScrollView scroll, LinearLayout painel) {
        FrameLayout tela = new FrameLayout(this);
        ImageView fundo = new ImageView(this);
        fundo.setImageResource(R.drawable.login_storm_background);
        fundo.setScaleType(ImageView.ScaleType.CENTER_CROP);
        tela.addView(fundo, new FrameLayout.LayoutParams(-1, -1));
        View sombreado = new View(this);
        sombreado.setBackgroundColor(Color.argb(34, 0, 16, 10));
        tela.addView(sombreado, new FrameLayout.LayoutParams(-1, -1));

        scroll.setBackgroundColor(Color.TRANSPARENT);
        ScrollView.LayoutParams painelParams = new ScrollView.LayoutParams(-1, -2);
        painelParams.setMargins(dp(16), dp(20), dp(16), dp(24));
        GradientDrawable vidro = new GradientDrawable();
        vidro.setColor(Color.argb(224, 250, 252, 250));
        vidro.setCornerRadius(dp(22));
        vidro.setStroke(dp(1), Color.argb(190, 220, 232, 224));
        painel.setBackground(vidro);
        scroll.addView(painel, painelParams);
        tela.addView(scroll, new FrameLayout.LayoutParams(-1, -1));
        return tela;
    }

    private void realizarLoginSistema(String usuario, String senha, Button botaoEntrar) {
        if (usuario.isEmpty() || senha.isEmpty()) {
            aviso("Informe usuário e senha.");
            return;
        }
        esconderTeclado();
        botaoEntrar.setEnabled(false);
        botaoEntrar.setText("Entrando...");
        new Thread(() -> {
            try {
                JSONObject resposta = postarLogin(usuario, senha);
                salvarSessaoSistema(resposta);
                runOnUiThread(() -> {
                    botaoEntrar.setEnabled(true);
                    botaoEntrar.setText("Entrar");
                    perguntarAtivarBiometriaAposLogin();
                });
            } catch (Exception e) {
                runOnUiThread(() -> {
                    botaoEntrar.setEnabled(true);
                    botaoEntrar.setText("Entrar");
                    new AlertDialog.Builder(this)
                        .setTitle("Não foi possível entrar")
                        .setMessage(mensagemErroSimples(e))
                        .setPositiveButton("OK", null)
                        .show();
                });
            }
        }).start();
    }

    private void perguntarAtivarBiometriaAposLogin() {
        if (biometriaAtiva()) {
            iniciarAppLogado();
            return;
        }
        if (!biometriaDisponivel()) {
            iniciarAppLogado();
            return;
        }
        carregarMensagemMotivacional(mensagem -> {
            LinearLayout painel = coluna(); painel.setPadding(dp(20), dp(10), dp(20), dp(4));
            TextView frase = texto(mensagem.isEmpty() ? "A mensagem motivacional do ERP aparecerá aqui quando estiver disponível." : mensagem, 17, true);
            frase.setGravity(Gravity.CENTER); frase.setPadding(dp(12), dp(20), dp(12), dp(20));
            frase.setBackground(fundoComBorda(Color.rgb(240, 248, 242), Color.rgb(198, 222, 203), 16));
            painel.addView(frase);
            new AlertDialog.Builder(this).setTitle("Proteja seu acesso")
                .setMessage("Uma mensagem para começar o dia. Escolha como deseja entrar neste aparelho.")
                .setView(painel)
                .setNegativeButton("Continuar sem biometria", (d, w) -> { setBiometriaAtiva(false); iniciarAppLogado(); })
                .setPositiveButton("Ativar biometria", (d, w) -> autenticarBiometria("Ativar biometria", () -> { setBiometriaAtiva(true); iniciarAppLogado(); }))
                .show();
        });
    }

    private void mostrarTelaBiometria() {
        telaAtual = "auth";
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        LinearLayout raiz = coluna();
        raiz.setPadding(dp(24), dp(36), dp(24), dp(32));
        ImageView logo = new ImageView(this);
        logo.setImageResource(com.exemplo.vendaswhatsapp.R.drawable.logo);
        logo.setScaleType(ImageView.ScaleType.CENTER_CROP);
        LinearLayout.LayoutParams logoParams = new LinearLayout.LayoutParams(dp(118), dp(118));
        logoParams.gravity = Gravity.CENTER_HORIZONTAL;
        raiz.addView(logo, logoParams);
        TextView titulo = texto("Use sua biometria para entrar", 23, true);
        titulo.setGravity(Gravity.CENTER_HORIZONTAL);
        raiz.addView(titulo);
        TextView status = texto("Biometria ativada neste aparelho.", 14, false);
        status.setGravity(Gravity.CENTER_HORIZONTAL);
        status.setPadding(0, 0, 0, dp(14));
        raiz.addView(status);
        TextView mensagemDoDia = texto("Carregando a mensagem motivacional do ERP...", 16, true);
        mensagemDoDia.setGravity(Gravity.CENTER);
        mensagemDoDia.setPadding(dp(18), dp(22), dp(18), dp(22));
        mensagemDoDia.setBackground(fundoComBorda(Color.rgb(240, 248, 242), Color.rgb(198, 222, 203), 16));
        LinearLayout.LayoutParams mensagemParams = new LinearLayout.LayoutParams(-1, -2);
        mensagemParams.setMargins(0, 0, 0, dp(18));
        raiz.addView(mensagemDoDia, mensagemParams);
        carregarMensagemMotivacional(mensagem -> mensagemDoDia.setText(mensagem.isEmpty()
            ? "Que seu trabalho de hoje renda bons frutos."
            : mensagem));
        Button usar = botao("Usar biometria", Color.rgb(21, 128, 61));
        usar.setOnClickListener(v -> autenticarBiometria("Entrar no app", () -> iniciarAppLogado()));
        raiz.addView(usar);
        Button umaVez = botao("Entrar sem biometria nesta vez", Color.rgb(75, 85, 99));
        umaVez.setOnClickListener(v -> iniciarAppLogado());
        raiz.addView(umaVez);
        Button sair = botao("Sair da conta", Color.rgb(185, 28, 28));
        LinearLayout.LayoutParams sairParams = new LinearLayout.LayoutParams(-1, -2);
        sairParams.setMargins(0, dp(8), 0, 0);
        sair.setLayoutParams(sairParams);
        sair.setOnClickListener(v -> sairDaConta(true));
        raiz.addView(sair);
        setContentView(montarTelaAutenticacao(scroll, raiz));
    }

    private interface MensagemMotivacionalCallback { void aoCarregar(String mensagem); }

    private void carregarMensagemMotivacional(MensagemMotivacionalCallback callback) {
        String salva = getSharedPreferences("daily_motivation", MODE_PRIVATE).getString("message", "").trim();
        new Thread(() -> {
            String mensagem = salva;
            try {
                JSONObject json = buscarObjetoApi("/api/mobile/daily-motivation");
                mensagem = json.optString("message", "").trim();
                String horario = json.optString("time", "07:00");
                getSharedPreferences("daily_motivation", MODE_PRIVATE).edit()
                    .putString("message", mensagem).putString("title", json.optString("title", "Mensagem do dia"))
                    .putString("date", json.optString("date", new SimpleDateFormat("yyyy-MM-dd", Locale.US).format(Calendar.getInstance().getTime())))
                    .putString("time", horario).putBoolean("enabled", json.optBoolean("enabled", false)).apply();
                if (adminNotificacoes() && json.optBoolean("enabled", false) && !mensagem.isEmpty()) DailyMotivationReceiver.agendar(this, horario);
            } catch (Exception ignored) { }
            final String finalMensagem = mensagem;
            if (callback != null) runOnUiThread(() -> callback.aoCarregar(finalMensagem));
        }).start();
    }

    private boolean biometriaDisponivel() {
        try {
            return BiometricManager.from(this).canAuthenticate(BiometricManager.Authenticators.BIOMETRIC_WEAK) == BiometricManager.BIOMETRIC_SUCCESS;
        } catch (Exception e) {
            return false;
        }
    }

    private boolean biometriaAtiva() {
        return authPrefs().getBoolean("biometria_ativa", false);
    }

    private void setBiometriaAtiva(boolean ativa) {
        authPrefs().edit().putBoolean("biometria_ativa", ativa).apply();
    }

    private void autenticarBiometria(String titulo, Runnable sucesso) {
        if (!biometriaDisponivel()) {
            aviso("A biometria nao esta disponivel neste aparelho.");
            return;
        }
        Executor executor = ContextCompat.getMainExecutor(this);
        BiometricPrompt prompt = new BiometricPrompt(this, executor, new BiometricPrompt.AuthenticationCallback() {
            @Override public void onAuthenticationSucceeded(BiometricPrompt.AuthenticationResult result) {
                super.onAuthenticationSucceeded(result);
                if (sucesso != null) sucesso.run();
            }
            @Override public void onAuthenticationError(int errorCode, CharSequence errString) {
                super.onAuthenticationError(errorCode, errString);
                aviso("Biometria cancelada ou indisponivel. Tente novamente.");
            }
            @Override public void onAuthenticationFailed() {
                super.onAuthenticationFailed();
                aviso("Biometria nao reconhecida.");
            }
        });
        BiometricPrompt.PromptInfo info = new BiometricPrompt.PromptInfo.Builder()
            .setTitle(titulo)
            .setSubtitle("Confirme sua identidade para continuar")
            .setNegativeButtonText("Cancelar")
            .setAllowedAuthenticators(BiometricManager.Authenticators.BIOMETRIC_WEAK)
            .build();
        prompt.authenticate(info);
    }

    private void mostrarCriarPin() {
        telaAtual = "auth";
        ScrollView scroll = new ScrollView(this);
        LinearLayout raiz = coluna();
        raiz.setPadding(dp(24), dp(32), dp(24), dp(32));
        scroll.addView(raiz);

        TextView titulo = texto("Criar PIN do app", 25, true);
        titulo.setGravity(Gravity.CENTER_HORIZONTAL);
        titulo.setTextColor(Color.rgb(20, 83, 45));
        raiz.addView(titulo);
        TextView subtitulo = texto("Esse PIN fica somente neste celular e serve para desbloquear o app.", 15, false);
        subtitulo.setGravity(Gravity.CENTER_HORIZONTAL);
        subtitulo.setPadding(0, 0, 0, dp(18));
        raiz.addView(subtitulo);

        EditText pin1 = campoPin("Digite 4 números");
        EditText pin2 = campoPin("Confirme o PIN");
        raiz.addView(texto("PIN", 13, false));
        raiz.addView(pin1);
        raiz.addView(texto("Confirmar PIN", 13, false));
        raiz.addView(pin2);

        Button salvar = botao("Salvar PIN", Color.rgb(21, 128, 61));
        salvar.setOnClickListener(v -> {
            String a = pin1.getText().toString().trim();
            String b = pin2.getText().toString().trim();
            if (!a.matches("\\d{4}") || !b.matches("\\d{4}")) {
                aviso("O PIN precisa ter exatamente 4 números.");
                return;
            }
            if (!a.equals(b)) {
                aviso("Os PINs não conferem.");
                return;
            }
            salvarPin(a);
            renovarDesbloqueioPin();
            esconderTeclado();
            iniciarAppLogado();
        });
        raiz.addView(salvar);

        Button sair = botao("Sair desta conta", Color.rgb(107, 114, 128));
        sair.setOnClickListener(v -> sairDaConta(false));
        raiz.addView(sair);
        setContentView(scroll);
        pin1.requestFocus();
        pin1.postDelayed(() -> mostrarTeclado(pin1), 250);
    }

    private void mostrarDesbloqueioPin() {
        telaAtual = "auth";
        ScrollView scroll = new ScrollView(this);
        LinearLayout raiz = coluna();
        raiz.setPadding(dp(24), dp(36), dp(24), dp(32));
        scroll.addView(raiz);

        TextView titulo = texto("Desbloquear app", 25, true);
        titulo.setGravity(Gravity.CENTER_HORIZONTAL);
        titulo.setTextColor(Color.rgb(20, 83, 45));
        raiz.addView(titulo);
        String nome = authPrefs().getString("full_name", "");
        TextView subtitulo = texto(nome.isEmpty() ? "Digite seu PIN de 4 dígitos." : "Olá, " + nome + ". Digite seu PIN.", 15, false);
        subtitulo.setGravity(Gravity.CENTER_HORIZONTAL);
        subtitulo.setPadding(0, 0, 0, dp(18));
        raiz.addView(subtitulo);

        EditText pin = campoPin("PIN de 4 dígitos");
        raiz.addView(pin);

        Button entrar = botao("Desbloquear", Color.rgb(21, 128, 61));
        entrar.setOnClickListener(v -> {
            String digitado = pin.getText().toString().trim();
            if (!pinConfere(digitado)) {
                pin.setText("");
                aviso("PIN incorreto.");
                return;
            }
            esconderTeclado();
            validarSessaoEEntrar(entrar);
        });
        raiz.addView(entrar);

        Button trocar = botao("Trocar usuário", Color.rgb(107, 114, 128));
        trocar.setOnClickListener(v -> sairDaConta(false));
        raiz.addView(trocar);
        setContentView(scroll);
        pin.requestFocus();
        pin.postDelayed(() -> mostrarTeclado(pin), 250);
    }

    private void validarSessaoEEntrar(Button botaoEntrar) {
        botaoEntrar.setEnabled(false);
        botaoEntrar.setText("Validando...");
        new Thread(() -> {
            try {
                JSONObject me = buscarAuthMe();
                atualizarUsuarioSessao(me);
                renovarDesbloqueioPin();
                runOnUiThread(() -> iniciarAppLogado());
            } catch (Exception e) {
                if (e instanceof SessaoExpiradaException) {
                    limparCredenciaisSessaoExpirada();
                    runOnUiThread(() -> new AlertDialog.Builder(this)
                        .setTitle("Sessão expirada")
                        .setMessage("A sessão do servidor expirou. Entre novamente com usuário e senha.")
                        .setPositiveButton("Entrar", (d, w) -> mostrarLoginSistema())
                        .show());
                } else {
                    runOnUiThread(() -> mostrarFalhaDeConexao(() -> validarSessaoEEntrar(botaoEntrar)));
                }
            }
        }).start();
    }

    private JSONObject postarLogin(String usuario, String senha) throws Exception {
        JSONObject body = new JSONObject();
        body.put("username", usuario);
        body.put("password", senha);
        HttpURLConnection conexao = null;
        try {
            byte[] conteudo = body.toString().getBytes("UTF-8");
            conexao = (HttpURLConnection) new URL(AUTH_LOGIN_URL).openConnection();
            conexao.setRequestMethod("POST");
            conexao.setDoOutput(true);
            conexao.setConnectTimeout(12000);
            conexao.setReadTimeout(25000);
            conexao.setRequestProperty("Content-Type", "application/json; charset=UTF-8");
            conexao.setRequestProperty("Accept", "application/json");
            conexao.setRequestProperty("x-client-type", "android");
            conexao.setFixedLengthStreamingMode(conteudo.length);
            try (java.io.OutputStream saida = conexao.getOutputStream()) { saida.write(conteudo); }
            int status = conexao.getResponseCode();
            byte[] resposta = lerFluxo(status >= 200 && status < 300 ? conexao.getInputStream() : conexao.getErrorStream());
            String texto = new String(resposta, "UTF-8");
            if (status < 200 || status >= 300) throw new Exception(texto.isEmpty() ? "erro " + status : texto);
            return new JSONObject(texto);
        } finally {
            if (conexao != null) conexao.disconnect();
        }
    }

    private JSONObject buscarAuthMe() throws Exception {
        HttpURLConnection conexao = null;
        try {
            conexao = (HttpURLConnection) new URL(AUTH_ME_URL).openConnection();
            conexao.setRequestMethod("GET");
            conexao.setConnectTimeout(10000);
            conexao.setReadTimeout(18000);
            conexao.setRequestProperty("Accept", "application/json");
            conexao.setRequestProperty("x-token", tokenSistema());
            int status = conexao.getResponseCode();
            byte[] resposta = lerFluxo(status >= 200 && status < 300 ? conexao.getInputStream() : conexao.getErrorStream());
            String texto = new String(resposta, "UTF-8");
            if (status == 401 || status == 403) throw new SessaoExpiradaException(texto.isEmpty() ? "Sessão expirada." : texto);
            if (status < 200 || status >= 300) throw new Exception(texto.isEmpty() ? "erro " + status : texto);
            return new JSONObject(texto);
        } finally {
            if (conexao != null) conexao.disconnect();
        }
    }

    private void enviarLogoutServidor(String token) {
        if (token == null || token.trim().isEmpty()) return;
        new Thread(() -> {
            HttpURLConnection conexao = null;
            try {
                conexao = (HttpURLConnection) new URL(AUTH_LOGOUT_URL).openConnection();
                conexao.setRequestMethod("POST");
                conexao.setConnectTimeout(6000);
                conexao.setReadTimeout(8000);
                conexao.setRequestProperty("x-token", token);
                conexao.getResponseCode();
            } catch (Exception ignored) {
            } finally {
                if (conexao != null) conexao.disconnect();
            }
        }).start();
    }

    private void salvarSessaoSistema(JSONObject resposta) throws Exception {
        String token = resposta.optString("token", "").trim();
        if (token.isEmpty()) throw new Exception("O servidor não retornou token.");
        authPrefs().edit()
            .putString("token", token)
            .putString("username", resposta.optString("username", ""))
            .putString("full_name", resposta.optString("full_name", ""))
            .putString("role", resposta.optString("role", ""))
            .putString("company", resposta.optString("company", ""))
            .putLong("login_at", System.currentTimeMillis())
            .apply();
        limparDadosPinAntigos();
    }

    private void atualizarUsuarioSessao(JSONObject me) {
        authPrefs().edit()
            .putString("username", me.optString("username", authPrefs().getString("username", "")))
            .putString("full_name", me.optString("full_name", authPrefs().getString("full_name", "")))
            .putString("role", me.optString("role", authPrefs().getString("role", "")))
            .putLong("last_validated_at", System.currentTimeMillis())
            .apply();
    }

    private SharedPreferences authPrefs() {
        try {
            MasterKey masterKey = new MasterKey.Builder(this)
                .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
                .build();
            SharedPreferences seguro = EncryptedSharedPreferences.create(
                this,
                "auth_sistema_seguro",
                masterKey,
                EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
                EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
            );
            migrarSessaoLegada(seguro);
            return seguro;
        } catch (Exception e) {
            return getSharedPreferences("auth_sistema", MODE_PRIVATE);
        }
    }

    static String tokenAdminParaAlertas(Context contexto) {
        try {
            MasterKey masterKey = new MasterKey.Builder(contexto)
                .setKeyScheme(MasterKey.KeyScheme.AES256_GCM).build();
            SharedPreferences prefs = EncryptedSharedPreferences.create(contexto, "auth_sistema_seguro", masterKey,
                EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
                EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM);
            String role = prefs.getString("role", "").trim();
            String token = prefs.getString("token", "").trim();
            if ("admin".equalsIgnoreCase(role) && !token.isEmpty()) return token;
            // authPrefs() deliberately falls back to the legacy store if Android
            // cannot open EncryptedSharedPreferences on a device. Keep the
            // receiver's check consistent with the active session in that case.
            if (!token.isEmpty() || !role.isEmpty()) return "";
        } catch (Exception e) {
            // Continue with the same legacy store used by authPrefs() fallback.
        }
        SharedPreferences legado = contexto.getSharedPreferences("auth_sistema", Context.MODE_PRIVATE);
        if (!"admin".equalsIgnoreCase(legado.getString("role", "").trim())) return "";
        return legado.getString("token", "").trim();
    }

    private boolean adminNotificacoes() {
        return !tokenSistema().isEmpty() && "admin".equalsIgnoreCase(authPrefs().getString("role", "").trim());
    }

    private void migrarSessaoLegada(SharedPreferences destino) {
        SharedPreferences legado = getSharedPreferences("auth_sistema", MODE_PRIVATE);
        String tokenLegado = legado.getString("token", "").trim();
        if (!tokenLegado.isEmpty() && destino.getString("token", "").trim().isEmpty()) {
            destino.edit()
                .putString("token", tokenLegado)
                .putString("username", legado.getString("username", ""))
                .putString("full_name", legado.getString("full_name", ""))
                .putString("role", legado.getString("role", ""))
                .putString("company", legado.getString("company", ""))
                .putLong("login_at", legado.getLong("login_at", 0L))
                .putLong("last_validated_at", legado.getLong("last_validated_at", 0L))
                .putBoolean("biometria_ativa", legado.getBoolean("biometria_ativa", false))
                .apply();
        }
        legado.edit()
            .remove("pin_hash")
            .remove("pin_salt")
            .remove("pin_unlocked_until")
            .apply();
        destino.edit()
            .remove("pin_hash")
            .remove("pin_salt")
            .remove("pin_unlocked_until")
            .apply();
    }

    private String tokenSistema() {
        return authPrefs().getString("token", "").trim();
    }

    private boolean pinConfigurado() {
        return !authPrefs().getString("pin_hash", "").isEmpty() && !authPrefs().getString("pin_salt", "").isEmpty();
    }

    private boolean pinAindaConfiavel() {
        long ate = authPrefs().getLong("pin_unlocked_until", 0L);
        return ate > System.currentTimeMillis();
    }

    private void renovarDesbloqueioPin() {
        authPrefs().edit()
            .putLong("pin_unlocked_until", System.currentTimeMillis() + PIN_TEMPO_CONFIAVEL_MS)
            .apply();
    }

    private void salvarPin(String pin) {
        String salt = UUID.randomUUID().toString();
        authPrefs().edit()
            .putString("pin_salt", salt)
            .putString("pin_hash", hashPin(pin, salt))
            .apply();
    }

    private boolean pinConfere(String pin) {
        if (pin == null || !pin.matches("\\d{4}")) return false;
        String salt = authPrefs().getString("pin_salt", "");
        String salvo = authPrefs().getString("pin_hash", "");
        return !salt.isEmpty() && !salvo.isEmpty() && salvo.equals(hashPin(pin, salt));
    }

    private String hashPin(String pin, String salt) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] bytes = digest.digest((salt + ":" + pin).getBytes("UTF-8"));
            return hexadecimal(bytes);
        } catch (Exception e) {
            return "";
        }
    }

    private void limparSessaoSistema() {
        authPrefs().edit()
            .remove("token")
            .remove("username")
            .remove("full_name")
            .remove("role")
            .remove("company")
            .remove("login_at")
            .remove("last_validated_at")
            .remove("biometria_ativa")
            .remove("pin_hash")
            .remove("pin_salt")
            .remove("pin_unlocked_until")
            .apply();
        getSharedPreferences("auth_sistema", MODE_PRIVATE).edit()
            .remove("token")
            .remove("username")
            .remove("full_name")
            .remove("role")
            .remove("company")
            .remove("login_at")
            .remove("last_validated_at")
            .remove("biometria_ativa")
            .remove("pin_hash")
            .remove("pin_salt")
            .remove("pin_unlocked_until")
            .apply();
        servicosPosLoginIniciados = false;
        CalendarNotificationReceiver.cancelar(this);
        NewTempoCollectionReceiver.cancelar(this);
    }

    private void limparCredenciaisSessaoExpirada() {
        authPrefs().edit()
            .remove("token").remove("username").remove("full_name").remove("role")
            .remove("company").remove("login_at").remove("last_validated_at")
            .remove("pin_hash").remove("pin_salt").remove("pin_unlocked_until")
            .apply();
        getSharedPreferences("auth_sistema", MODE_PRIVATE).edit()
            .remove("token").remove("username").remove("full_name").remove("role")
            .remove("company").remove("login_at").remove("last_validated_at")
            .remove("pin_hash").remove("pin_salt").remove("pin_unlocked_until")
            .apply();
        servicosPosLoginIniciados = false;
        CalendarNotificationReceiver.cancelar(this);
        NewTempoCollectionReceiver.cancelar(this);
    }

    private void mostrarFalhaDeConexao(Runnable tentarNovamente) {
        new AlertDialog.Builder(this)
            .setTitle("Sem conexão com o servidor")
            .setMessage("Não foi possível validar seu acesso. Sua sessão e biometria foram preservadas; verifique a internet e tente novamente.")
            .setPositiveButton("Tentar novamente", (d, w) -> tentarNovamente.run())
            .setNegativeButton("Fechar", null)
            .show();
    }

    private void limparDadosPinAntigos() {
        authPrefs().edit()
            .remove("pin_hash")
            .remove("pin_salt")
            .remove("pin_unlocked_until")
            .apply();
        getSharedPreferences("auth_sistema", MODE_PRIVATE).edit()
            .remove("pin_hash")
            .remove("pin_salt")
            .remove("pin_unlocked_until")
            .apply();
    }

    private void limparContaLocal() {
        limparSessaoSistema();
        authPrefs().edit().clear().apply();
        getSharedPreferences("auth_sistema", MODE_PRIVATE).edit().clear().apply();
    }

    private void sairDaConta(boolean perguntar) {
        Runnable executar = () -> {
            String token = tokenSistema();
            enviarLogoutServidor(token);
            limparContaLocal();
            abrirFluxoInicial();
        };
        if (!perguntar) {
            executar.run();
            return;
        }
        new AlertDialog.Builder(this)
            .setTitle("Sair da conta?")
            .setMessage("A sessão e a biometria deste aparelho serão removidas. Para usar novamente, será necessário entrar com usuário e senha do sistema.")
            .setNegativeButton("Cancelar", null)
            .setPositiveButton("Sair", (d, w) -> executar.run())
            .show();
    }

    private EditText campoPin(String dica) {
        EditText e = campo(dica, InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_VARIATION_PASSWORD);
        e.setKeyListener(DigitsKeyListener.getInstance("0123456789"));
        e.setSingleLine(true);
        return e;
    }

    private String mensagemErroSimples(Exception e) {
        String msg = e == null ? "" : String.valueOf(e.getMessage());
        if (msg.contains("detail")) {
            try { return new JSONObject(msg).optString("detail", msg); }
            catch (Exception ignored) { }
        }
        if (msg.toLowerCase(new Locale("pt", "BR")).contains("failed to connect") || msg.toLowerCase(new Locale("pt", "BR")).contains("timeout")) {
            return "Sem conexão com o servidor. Verifique a internet e tente novamente.";
        }
        return msg.isEmpty() ? "Erro inesperado. Tente novamente." : msg;
    }

    private View criarTela() {
        rascunhoPronto = false;
        listenersRascunhoAtivos = false;
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(COR_FUNDO_ESCURO);
        LinearLayout raiz = coluna();
        raiz.setBackgroundColor(COR_FUNDO_ESCURO);
        raiz.setPadding(dp(16), dp(10), dp(16), dp(24));
        scroll.addView(raiz);

        LinearLayout topo = new LinearLayout(this);
        topo.setOrientation(LinearLayout.HORIZONTAL);
        topo.setGravity(Gravity.CENTER_VERTICAL);
        Button notasEnviadas = botao("Notas", Color.rgb(21, 128, 61));
        notasEnviadas.setTextSize(13);
        notasEnviadas.setOnClickListener(v -> mostrarNotasEnviadas());
        LinearLayout.LayoutParams notasParams = new LinearLayout.LayoutParams(dp(72), dp(42));
        notasParams.setMargins(0, 0, dp(8), 0);
        topo.addView(notasEnviadas, notasParams);
        LinearLayout marca = coluna();
        TextView nomeMarca = texto("MENINA DOS RAIOS", 13, true);
        nomeMarca.setTextColor(Color.rgb(20, 83, 45));
        marca.addView(nomeMarca);
        marca.addView(texto("OPERAÇÃO · PEDIDOS", 10, false));
        topo.addView(marca, new LinearLayout.LayoutParams(0, -2, 1));
        Button sino = botao("🔔", Color.rgb(79, 70, 229));
        sino.setTextSize(19);
        sino.setOnClickListener(v -> abrirCentralNotificacoes("calendario"));
        LinearLayout.LayoutParams sinoParams = new LinearLayout.LayoutParams(dp(44), dp(42));
        sinoParams.setMargins(dp(8), 0, 0, 0);
        if (adminNotificacoes()) topo.addView(sino, sinoParams);
        raiz.addView(topo);

        TextView titulo = texto("Nova entrega", 25, true);
        titulo.setTextColor(Color.rgb(20, 83, 45));
        titulo.setGravity(Gravity.START);
        titulo.setPadding(0, dp(13), 0, 0);
        raiz.addView(titulo);
        TextView subtitulo = texto("Monte o pedido e envie ao ERP.", 13, false);
        subtitulo.setGravity(Gravity.START);
        subtitulo.setPadding(0, 0, 0, dp(8));
        raiz.addView(subtitulo);
        adicionarEtapasPedido(raiz);

        Button colarPedido = botao("Importar pedido do WhatsApp", Color.WHITE);
        colarPedido.setTextSize(14);
        colarPedido.setTextColor(Color.rgb(20, 83, 45));
        colarPedido.setBackground(fundoComBorda(Color.WHITE, Color.rgb(21, 101, 52), 11));
        colarPedido.setOnClickListener(v -> abrirColagemWhatsApp());
        raiz.addView(colarPedido);

        adicionarTituloSecao(raiz, "01  ·  Cliente e data");
        raiz.addView(rotuloCampo("Cliente"));
        cliente = new Spinner(this);
        cliente.setAdapter(adaptadorSpinner(CLIENTES_PADRAO));
        cliente.setPadding(0, dp(8), 0, dp(8));
        estilizarSpinner(cliente, Color.rgb(55, 65, 81));
        clienteOutro = campo("Digite o nome do cliente", InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_CAP_CHARACTERS);
        clienteOutro.setVisibility(View.GONE);
        cliente.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {
            @Override public void onItemSelected(AdapterView<?> parent, View view, int position, long id) {
                boolean outro = "OUTRO".equals(parent.getItemAtPosition(position).toString());
                clienteOutro.setVisibility(outro ? View.VISIBLE : View.GONE);
                if (outro) clienteOutro.requestFocus();
                else clienteOutro.setText("");
                agendarSalvarRascunho();
            }
            @Override public void onNothingSelected(AdapterView<?> parent) { }
        });
        raiz.addView(rotuloCampo("Data da nota"));
        data = campo("Selecione a data", InputType.TYPE_CLASS_DATETIME);
        data.setFocusable(false);
        data.setOnClickListener(v -> escolherData());
        raiz.addView(cliente);
        raiz.addView(clienteOutro);
        raiz.addView(data);

        adicionarTituloSecao(raiz, "02  ·  Adicione produtos");
        carregarProdutos();
        produto = new Spinner(this);
        produtosAdapter = adaptadorSpinner(produtos);
        produto.setAdapter(produtosAdapter);
        produto.setPadding(0, dp(8), 0, dp(8));
        estilizarSpinner(produto, Color.rgb(55, 65, 81));
        produto.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {
            @Override public void onItemSelected(AdapterView<?> parent, View view, int position, long id) {
                atualizarDicaValor();
                selecionarUnidadeDoProduto(parent.getItemAtPosition(position).toString());
                if (produtoInicializado && peso != null) {
                    peso.requestFocus();
                    peso.postDelayed(() -> mostrarTeclado(peso), 150);
                }
                produtoInicializado = true;
                agendarSalvarRascunho();
            }
            @Override public void onNothingSelected(AdapterView<?> parent) { atualizarDicaValor(); }
        });
        peso = campo("Peso", InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_FLAG_DECIMAL);
        valor = campo("Valor unitário (R$)", InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_FLAG_DECIMAL);
        peso.setKeyListener(DigitsKeyListener.getInstance("0123456789,."));
        valor.setKeyListener(DigitsKeyListener.getInstance("0123456789,."));
        peso.setOnFocusChangeListener((v, foco) -> { if (foco) manterCampoVisivel(scroll, peso); });
        valor.setOnFocusChangeListener((v, foco) -> { if (foco) manterCampoVisivel(scroll, valor); });
        unidade = new Spinner(this);
        String[] unidades = {"KG", "UN", "CX", "MC", "SC"};
        unidade.setAdapter(adaptadorSpinner(unidades));
        unidade.setPadding(0, dp(8), 0, dp(8));
        unidade.setBackground(fundoComBorda(Color.rgb(254, 240, 138), Color.rgb(202, 138, 4), 10));
        unidade.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {
            @Override public void onItemSelected(AdapterView<?> parent, View view, int position, long id) {
                String codigo = parent.getItemAtPosition(position).toString();
                peso.setHint(rotuloMedida(codigo) + " (" + codigo + ")");
                agendarSalvarRascunho();
            }
            @Override public void onNothingSelected(AdapterView<?> parent) { peso.setHint("Peso"); }
        });
        if (produto.getSelectedItem() != null) selecionarUnidadeDoProduto(produto.getSelectedItem().toString());
        atualizarDicaValor();
        raiz.addView(rotuloCampo("Produto"));
        raiz.addView(produto);
        LinearLayout linhaMedidas = new LinearLayout(this);
        linhaMedidas.setOrientation(LinearLayout.HORIZONTAL);
        LinearLayout campoPeso = coluna();
        campoPeso.addView(rotuloCampo("Peso / quantidade"));
        campoPeso.addView(peso);
        LinearLayout campoValor = coluna();
        campoValor.addView(rotuloCampo("Valor unitário"));
        campoValor.addView(valor);
        LinearLayout.LayoutParams medidaParams = new LinearLayout.LayoutParams(0, -2, 1);
        medidaParams.setMargins(0, 0, dp(5), 0);
        linhaMedidas.addView(campoPeso, medidaParams);
        LinearLayout.LayoutParams valorParams = new LinearLayout.LayoutParams(0, -2, 1);
        valorParams.setMargins(dp(5), 0, 0, 0);
        linhaMedidas.addView(campoValor, valorParams);
        raiz.addView(linhaMedidas);

        Button adicionar = botao("Adicionar produto", Color.rgb(22, 101, 52));
        adicionar.setOnClickListener(v -> adicionarItem());
        raiz.addView(adicionar);

        adicionarTituloSecao(raiz, "03  ·  Revise o pedido");
        listaItens = coluna();
        raiz.addView(listaItens);
        totalText = texto("0 produtos\nTotal: " + moeda.format(0), 18, true);
        totalText.setTextColor(COR_TEXTO_CLARO);
        totalText.setGravity(Gravity.END | Gravity.CENTER_VERTICAL);
        totalText.setPadding(dp(12), dp(12), dp(12), dp(12));
        totalText.setBackground(fundoComBorda(COR_CARD_ESCURO, Color.rgb(216, 227, 220), 12));
        LinearLayout.LayoutParams resumoParams = new LinearLayout.LayoutParams(-1, -2);
        resumoParams.setMargins(0, dp(5), 0, dp(8));
        raiz.addView(totalText, resumoParams);

        enviarSistemaButton = botao("Enviar pedido ao ERP", Color.rgb(21, 101, 52));
        enviarSistemaButton.setOnClickListener(v -> enviarTexto());
        raiz.addView(enviarSistemaButton);
        statusEnvioView = texto("Pronto para enviar", 13, false);
        statusEnvioView.setPadding(dp(4), dp(2), dp(4), dp(6));
        raiz.addView(statusEnvioView);
        pendentesButton = botao("Notas pendentes de envio", Color.rgb(180, 83, 9));
        pendentesButton.setOnClickListener(v -> mostrarNotasPendentes());
        raiz.addView(pendentesButton);
        atualizarBotaoPendentes();
        atualizarLista();
        return scroll;
    }

    private TextView rotuloCampo(String rotulo) {
        TextView view = texto(rotulo, 13, true);
        view.setTextColor(COR_TEXTO_SUAVE);
        view.setPadding(0, dp(5), 0, dp(2));
        return view;
    }

    private void adicionarTituloSecao(LinearLayout raiz, String titulo) {
        TextView view = texto(titulo, 15, true);
        view.setTextColor(Color.rgb(20, 83, 45));
        view.setPadding(dp(11), dp(8), dp(11), dp(8));
        view.setBackground(fundoComBorda(Color.rgb(237, 245, 239), Color.rgb(220, 232, 223), 9));
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-1, -2);
        params.setMargins(0, dp(14), 0, dp(5));
        raiz.addView(view, params);
    }

    private void abrirModuloEntregas(boolean mostrarConcluidas) {
        temaEscuroAtivo = true;
        telaAtual = "entregas_lista";
        ScrollView scroll = new ScrollView(this);
        scroll.setBackgroundColor(COR_FUNDO_ESCURO);
        LinearLayout raiz = coluna();
        raiz.setBackgroundColor(COR_FUNDO_ESCURO);
        raiz.setPadding(dp(18), dp(16), dp(18), dp(26));
        scroll.addView(raiz);
        adicionarCabecalhoModulo(raiz, "Entregas", "Notas fiscais e confirmação de entrega.");

        LinearLayout filtros = new LinearLayout(this);
        filtros.setOrientation(LinearLayout.HORIZONTAL);
        Button pendentes = botaoFiltro("Pendentes", !mostrarConcluidas, () -> abrirModuloEntregas(false));
        Button concluidas = botaoFiltro("Concluídas", mostrarConcluidas, () -> abrirModuloEntregas(true));
        LinearLayout.LayoutParams p1 = new LinearLayout.LayoutParams(0, dp(46), 1);
        p1.setMargins(0, 0, dp(4), dp(6));
        LinearLayout.LayoutParams p2 = new LinearLayout.LayoutParams(0, dp(46), 1);
        p2.setMargins(dp(4), 0, 0, dp(6));
        filtros.addView(pendentes, p1);
        filtros.addView(concluidas, p2);
        raiz.addView(filtros);

        TextView resumo = texto("Carregando entregas...", 15, true);
        resumo.setGravity(Gravity.CENTER_HORIZONTAL);
        raiz.addView(resumo);
        LinearLayout lista = coluna();
        raiz.addView(lista);

        Button atualizar = botao("↻ Atualizar lista", Color.rgb(21, 101, 52));
        atualizar.setTextSize(13);
        atualizar.setOnClickListener(v -> carregarEntregas(lista, resumo, mostrarConcluidas, atualizar));
        raiz.addView(atualizar);

        setContentView(scroll);
        carregarEntregas(lista, resumo, mostrarConcluidas, atualizar);
    }

    private void carregarEntregas(LinearLayout lista, TextView resumo, boolean mostrarConcluidas, Button botaoAtualizar) {
        lista.removeAllViews();
        resumo.setText("Carregando entregas...");
        botaoAtualizar.setEnabled(false);
        botaoAtualizar.setText("Atualizando...");
        new Thread(() -> {
            try {
                JSONArray rows = buscarVendasEntrega();
                List<EntregaGrupo> grupos = agruparEntregas(rows, mostrarConcluidas);
                runOnUiThread(() -> {
                    lista.removeAllViews();
                    resumo.setText((mostrarConcluidas ? "Concluídas: " : "Pendentes: ") + grupos.size());
                    if (grupos.isEmpty()) {
                        lista.addView(texto(mostrarConcluidas ? "Nenhuma entrega concluída encontrada." : "Nenhuma entrega pendente encontrada.", 15, false));
                    } else {
                        for (EntregaGrupo g : grupos) lista.addView(cartaoEntrega(g, mostrarConcluidas, lista, resumo, botaoAtualizar));
                    }
                    botaoAtualizar.setEnabled(true);
                    botaoAtualizar.setText("Atualizar entregas");
                });
            } catch (Exception e) {
                runOnUiThread(() -> {
                    lista.removeAllViews();
                    resumo.setText("Erro ao carregar entregas");
                    lista.addView(texto(mensagemErroSimples(e), 14, false));
                    botaoAtualizar.setEnabled(true);
                    botaoAtualizar.setText("Atualizar entregas");
                });
            }
        }).start();
    }

    private JSONArray buscarVendasEntrega() throws Exception {
        HttpURLConnection conexao = null;
        try {
            String endereco = SALES_URL + "?sale_type=NF&limit=300";
            conexao = (HttpURLConnection) new URL(endereco).openConnection();
            conexao.setRequestMethod("GET");
            conexao.setConnectTimeout(12000);
            conexao.setReadTimeout(25000);
            conexao.setRequestProperty("Accept", "application/json");
            conexao.setRequestProperty("x-token", tokenSistema());
            int status = conexao.getResponseCode();
            byte[] resposta = lerFluxo(status >= 200 && status < 300 ? conexao.getInputStream() : conexao.getErrorStream());
            String texto = new String(resposta, "UTF-8");
            if (status < 200 || status >= 300) throw new Exception(texto.isEmpty() ? "erro " + status : texto);
            return new JSONArray(texto);
        } finally {
            if (conexao != null) conexao.disconnect();
        }
    }

    private List<EntregaGrupo> agruparEntregas(JSONArray rows, boolean concluidas) {
        LinkedHashMap<String, EntregaGrupo> mapa = new LinkedHashMap<>();
        for (int i = 0; i < rows.length(); i++) {
            JSONObject r = rows.optJSONObject(i);
            if (r == null) continue;
            boolean entregue = "sim".equalsIgnoreCase(r.optString("delivered", ""));
            if (concluidas != entregue) continue;
            String id = r.optString("id", "");
            String data = r.optString("sale_date", "");
            String cliente = nomeClienteMaiusculo(r.optString("client", ""));
            String nf = r.optString("nf_number", "");
            String entregador = r.optString("delivery_person", "");
            String chave = (nf.trim().isEmpty() ? id : (data + "|" + nf + "|" + cliente + "|" + entregador));
            EntregaGrupo g = mapa.get(chave);
            if (g == null) {
                g = new EntregaGrupo();
                g.data = data;
                g.hora = r.optString("sale_time", "");
                g.cliente = cliente;
                g.nf = nf;
                g.entregador = entregador;
                g.placa = r.optString("plate", "");
                g.entregue = entregue;
                g.entregueEm = r.optString("delivered_at", "");
                mapa.put(chave, g);
            }
            if (!id.isEmpty()) g.ids.add(id);
            g.produtos++;
            g.total += r.optDouble("total", 0);
            String produtoLinha = r.optString("product", "Produto");
            double qtd = r.optDouble("quantity", 0);
            if (g.itens.length() < 280) {
                if (g.itens.length() > 0) g.itens.append("\n");
                g.itens.append("• ").append(produtoLinha).append(" — ").append(formatarNumero(qtd));
            }
        }
        return new ArrayList<>(mapa.values());
    }

    private View cartaoEntrega(EntregaGrupo g, boolean mostrarConcluidas, LinearLayout lista, TextView resumo, Button botaoAtualizar) {
        LinearLayout card = coluna();
        int corStatus = mostrarConcluidas ? Color.rgb(34, 197, 94) : Color.rgb(245, 124, 0);
        card.setPadding(dp(14), dp(12), dp(14), dp(12));
        card.setBackground(fundoCardEscuro(corStatus));
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-1, -2);
        params.setMargins(0, dp(7), 0, dp(7));
        card.setLayoutParams(params);

        String titulo = (g.cliente == null || g.cliente.trim().isEmpty() ? "Cliente não informado" : nomeClienteMaiusculo(g.cliente));
        card.addView(texto(titulo, 18, true));
        String linha = "Data: " + dataBR(g.data) + (g.nf.trim().isEmpty() ? "" : "  •  NF: " + g.nf);
        card.addView(texto(linha, 13, false));
        String meta = g.produtos + " produto(s) • " + moeda.format(g.total);
        if (!g.entregador.trim().isEmpty()) meta += "\nEntregador: " + g.entregador;
        if (!g.placa.trim().isEmpty()) meta += " • Placa: " + g.placa;
        if (mostrarConcluidas && !g.entregueEm.trim().isEmpty()) meta += "\nConcluída em: " + g.entregueEm;
        card.addView(texto(meta, 14, false));

        if (g.itens.length() > 0) {
            TextView itensTxt = texto(g.itens.toString(), 13, false);
            itensTxt.setPadding(0, dp(6), 0, dp(4));
            card.addView(itensTxt);
        }

        LinearLayout acoes = new LinearLayout(this);
        acoes.setOrientation(LinearLayout.HORIZONTAL);
        Button ver = botao("Ver", Color.rgb(37, 99, 235));
        ver.setOnClickListener(v -> new AlertDialog.Builder(this)
            .setTitle(titulo)
            .setMessage("Data: " + dataBR(g.data) + "\nNF: " + (g.nf.trim().isEmpty() ? "—" : g.nf) + "\nTotal: " + moeda.format(g.total) + "\n\nProdutos:\n" + (g.itens.length() == 0 ? "Nenhum produto." : g.itens.toString()))
            .setPositiveButton("OK", null)
            .show());
        LinearLayout.LayoutParams verParams = new LinearLayout.LayoutParams(0, dp(42), 1);
        verParams.setMargins(0, dp(6), dp(4), 0);
        acoes.addView(ver, verParams);

        if (!mostrarConcluidas) {
            Button concluir = botao("Concluir", Color.rgb(21, 128, 61));
            concluir.setOnClickListener(v -> confirmarConcluirEntrega(g, lista, resumo, botaoAtualizar));
            LinearLayout.LayoutParams concluirParams = new LinearLayout.LayoutParams(0, dp(42), 1);
            concluirParams.setMargins(dp(4), dp(6), 0, 0);
            acoes.addView(concluir, concluirParams);
        }
        card.addView(acoes);
        card.setElevation(dp(4));
        aplicarFeedbackToque(card);
        return card;
    }

    private void confirmarConcluirEntrega(EntregaGrupo g, LinearLayout lista, TextView resumo, Button botaoAtualizar) {
        new AlertDialog.Builder(this)
            .setTitle("Concluir entrega?")
            .setMessage("Cliente: " + nomeClienteMaiusculo(g.cliente) + "\nNF: " + (g.nf.trim().isEmpty() ? "—" : g.nf) + "\nProdutos: " + g.produtos + "\n\nConfirmar como entregue hoje?")
            .setNegativeButton("Cancelar", null)
            .setPositiveButton("Concluir", (d, w) -> concluirEntrega(g, lista, resumo, botaoAtualizar))
            .show();
    }

    private void concluirEntrega(EntregaGrupo g, LinearLayout lista, TextView resumo, Button botaoAtualizar) {
        botaoAtualizar.setEnabled(false);
        new Thread(() -> {
            try {
                marcarEntregaConcluida(g);
                runOnUiThread(() -> {
                    aviso("Entrega concluída.");
                    carregarEntregas(lista, resumo, false, botaoAtualizar);
                });
            } catch (Exception e) {
                runOnUiThread(() -> {
                    botaoAtualizar.setEnabled(true);
                    new AlertDialog.Builder(this)
                        .setTitle("Não foi possível concluir")
                        .setMessage(mensagemErroSimples(e))
                        .setPositiveButton("OK", null)
                        .show();
                });
            }
        }).start();
    }

    private void marcarEntregaConcluida(EntregaGrupo g) throws Exception {
        JSONObject body = new JSONObject();
        JSONArray ids = new JSONArray();
        for (String id : g.ids) ids.put(id);
        body.put("ids", ids);
        body.put("delivered", "sim");
        body.put("delivered_at", new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", Locale.getDefault()).format(Calendar.getInstance().getTime()));
        HttpURLConnection conexao = null;
        try {
            byte[] conteudo = body.toString().getBytes("UTF-8");
            conexao = (HttpURLConnection) new URL(SALES_BULK_DELIVERED_URL).openConnection();
            conexao.setRequestMethod("PUT");
            conexao.setDoOutput(true);
            conexao.setConnectTimeout(12000);
            conexao.setReadTimeout(25000);
            conexao.setRequestProperty("Content-Type", "application/json; charset=UTF-8");
            conexao.setRequestProperty("Accept", "application/json");
            conexao.setRequestProperty("x-token", tokenSistema());
            conexao.setFixedLengthStreamingMode(conteudo.length);
            try (java.io.OutputStream saida = conexao.getOutputStream()) { saida.write(conteudo); }
            int status = conexao.getResponseCode();
            if (status < 200 || status >= 300) {
                String detalhe = new String(lerFluxo(conexao.getErrorStream()), "UTF-8");
                throw new Exception(detalhe.isEmpty() ? "erro " + status : detalhe);
            }
        } finally {
            if (conexao != null) conexao.disconnect();
        }
    }

    private String dataBR(String iso) {
        try {
            if (iso == null || iso.length() < 10) return iso == null ? "" : iso;
            return iso.substring(8, 10) + "/" + iso.substring(5, 7) + "/" + iso.substring(0, 4);
        } catch (Exception e) {
            return iso == null ? "" : iso;
        }
    }

    private void abrirColagemWhatsApp() {
        String copiado = textoCopiado();
        EditText entrada = new EditText(this);
        entrada.setHint("Cole aqui o pedido recebido no WhatsApp");
        entrada.setText(copiado);
        entrada.setMinLines(8);
        entrada.setGravity(Gravity.TOP | Gravity.START);
        entrada.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_MULTI_LINE | InputType.TYPE_TEXT_FLAG_CAP_SENTENCES);
        entrada.setSingleLine(false);
        entrada.setPadding(dp(12), dp(10), dp(12), dp(10));

        LinearLayout caixa = coluna();
        caixa.setPadding(dp(18), dp(4), dp(18), 0);
        TextView dica = texto("O app vai identificar produto, quantidade e unidade automaticamente.", 14, false);
        dica.setPadding(0, 0, 0, dp(8));
        caixa.addView(dica);
        caixa.addView(entrada, new LinearLayout.LayoutParams(-1, dp(220)));

        new AlertDialog.Builder(this)
            .setTitle("Colar pedido do WhatsApp")
            .setView(caixa)
            .setNegativeButton("Cancelar", null)
            .setPositiveButton("Interpretar", (dialog, which) -> processarTextoWhatsApp(entrada.getText().toString()))
            .show();
    }

    private void sugerirColagemWhatsAppAoAbrir() {
        String copiado = textoCopiado();
        if (copiado.trim().isEmpty() || !textoTemCaraDePedido(copiado)) return;
        String assinatura = String.valueOf(copiado.hashCode());
        String ultima = getSharedPreferences("importacao_whatsapp", MODE_PRIVATE).getString("ultima_sugestao", "");
        if (assinatura.equals(ultima)) return;
        new AlertDialog.Builder(this)
            .setTitle("Pedido copiado encontrado")
            .setMessage("Parece que existe um pedido do WhatsApp copiado. Deseja colar e interpretar agora?")
            .setNegativeButton("Agora não", (d, w) -> salvarUltimaSugestaoColagem(assinatura))
            .setPositiveButton("Colar pedido", (d, w) -> {
                salvarUltimaSugestaoColagem(assinatura);
                processarTextoWhatsApp(copiado);
            })
            .show();
    }

    private void salvarUltimaSugestaoColagem(String assinatura) {
        getSharedPreferences("importacao_whatsapp", MODE_PRIVATE).edit().putString("ultima_sugestao", assinatura).apply();
    }

    private boolean textoTemCaraDePedido(String texto) {
        int reconhecidos = 0;
        for (String linha : texto.replace("\r", "\n").split("\n")) {
            if (interpretarLinhaPedido(linha) != null) reconhecidos++;
            if (reconhecidos >= 2) return true;
        }
        String n = normalizarNomeProduto(texto);
        return n.contains(" KG") || n.contains(" UND") || n.contains(" CX") || n.contains(" MÇ") || n.contains(" MC") || n.contains(" SC");
    }

    private String textoCopiado() {
        try {
            ClipboardManager clipboard = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
            if (clipboard == null || !clipboard.hasPrimaryClip() || clipboard.getPrimaryClip() == null) return "";
            if (clipboard.getPrimaryClip().getItemCount() == 0) return "";
            CharSequence texto = clipboard.getPrimaryClip().getItemAt(0).coerceToText(this);
            return texto == null ? "" : texto.toString();
        } catch (Exception e) {
            return "";
        }
    }

    private void processarTextoWhatsApp(String texto) {
        if (texto == null || texto.trim().isEmpty()) {
            aviso("Cole o texto do WhatsApp para interpretar.");
            return;
        }

        List<ItemInterpretado> encontrados = new ArrayList<>();
        List<String> ignorados = new ArrayList<>();
        String[] linhas = texto.replace("\r", "\n").split("\n");
        for (String linha : linhas) {
            ItemInterpretado item = interpretarLinhaPedido(linha);
            if (item != null) encontrados.add(item);
            else if (linha != null && linha.trim().length() > 0 && pareceLinhaDeProduto(linha)) ignorados.add(linha.trim());
        }

        if (encontrados.isEmpty()) {
            aviso("Não consegui identificar produtos nesse texto.");
            return;
        }

        Runnable adicionar = () -> {
            for (ItemInterpretado item : encontrados) {
                itens.add(new ItemPedido(item.produto, item.medida, item.unidade, 0, false));
            }
            atualizarLista();
            StringBuilder resumo = new StringBuilder();
            resumo.append(encontrados.size()).append(encontrados.size() == 1 ? " produto identificado." : " produtos identificados.");
            if (!ignorados.isEmpty()) {
                resumo.append("\n\nNão consegui ler estas linhas:\n");
                int limite = Math.min(ignorados.size(), 6);
                for (int i = 0; i < limite; i++) resumo.append("- ").append(ignorados.get(i)).append("\n");
                if (ignorados.size() > limite) resumo.append("- ...\n");
            }
            new AlertDialog.Builder(this)
                .setTitle("Pedido importado")
                .setMessage(resumo.toString())
                .setPositiveButton("Escolher cliente", (d, w) -> confirmarClienteAposColagem(texto))
                .show();
        };

        if (!itens.isEmpty()) {
            new AlertDialog.Builder(this)
                .setTitle("Já existem produtos na nota")
                .setMessage("Deseja adicionar os produtos copiados junto com os produtos que já estão na tela?")
                .setNegativeButton("Cancelar", null)
                .setNeutralButton("Limpar e importar", (d, w) -> { itens.clear(); adicionar.run(); })
                .setPositiveButton("Adicionar junto", (d, w) -> adicionar.run())
                .show();
        } else {
            adicionar.run();
        }
    }

    private void confirmarClienteAposColagem(String textoOriginal) {
        int sugerido = indiceClienteSugerido(textoOriginal);
        final int[] escolhido = {Math.max(0, sugerido)};
        new AlertDialog.Builder(this)
            .setTitle("Para qual cliente enviar?")
            .setSingleChoiceItems(CLIENTES_PADRAO, escolhido[0], (dialog, which) -> escolhido[0] = which)
            .setNegativeButton("Cancelar", null)
            .setPositiveButton("Continuar", (dialog, which) -> selecionarClienteImportado(escolhido[0]))
            .show();
    }

    private void selecionarClienteImportado(int indice) {
        if (indice < 0 || indice >= CLIENTES_PADRAO.length) indice = 0;
        String nome = CLIENTES_PADRAO[indice];
        cliente.setSelection(indice);
        if ("OUTRO".equals(nome)) {
            EditText entrada = campo("Nome do cliente", InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_CAP_CHARACTERS);
            new AlertDialog.Builder(this)
                .setTitle("Digite o cliente")
                .setView(entrada)
                .setNegativeButton("Cancelar", null)
                .setPositiveButton("Continuar", (d, w) -> {
                    clienteOutro.setText(entrada.getText().toString().trim().toUpperCase(new Locale("pt", "BR")));
                    confirmarEnvioAposColagem();
                })
                .show();
        } else {
            clienteOutro.setText("");
            confirmarEnvioAposColagem();
        }
    }

    private void confirmarEnvioAposColagem() {
        new AlertDialog.Builder(this)
            .setTitle("Enviar para o sistema?")
            .setMessage("Cliente: " + obterCliente() + "\nProdutos: " + itens.size() + "\n\nDeseja enviar agora?")
            .setNegativeButton("Não, deixar na tela", null)
            .setPositiveButton("Enviar agora", (d, w) -> enviarTexto())
            .show();
    }

    private int indiceClienteSugerido(String texto) {
        String n = normalizarNomeProduto(texto);
        if (n.contains("PALADAR BASE") || n.contains("HORTI BASE") || n.contains(" BASE")) return 1;
        if (n.contains("SESAU")) return 2;
        if (n.contains("MATERNIDADE") || n.contains("MARIA DA CONSOLACAO")) return 3;
        if (n.contains("HGR")) return 4;
        if (n.contains("PALADAR DISTRITO") || n.contains("UND HGR") || n.contains("DISTRITO")) return 0;
        return 0;
    }

    private ItemInterpretado interpretarLinhaPedido(String linhaOriginal) {
        if (linhaOriginal == null) return null;
        String linha = limparLinhaPedido(linhaOriginal);
        if (linha.isEmpty() || deveIgnorarLinhaPedido(linha)) return null;

        ItemInterpretado flexivel = interpretarProdutoQuantidadeEmQualquerOrdem(linha);
        if (flexivel != null) return flexivel;

        ItemInterpretado porIgual = interpretarComPadrao(linha, "^(.+?)\\s*[=:]\\s*([0-9]+(?:[\\.,][0-9]+)?)\\s*([A-Za-zÀ-ÿçÇãÃõÕéÉíÍóÓúÚüÜ]+)\\.?$");
        if (porIgual != null) return porIgual;

        Matcher quantidadePrimeiro = Pattern.compile("^([0-9]+(?:[\\.,][0-9]+)?)\\s*([A-Za-zÀ-ÿçÇãÃõÕéÉíÍóÓúÚüÜ]+)\\s+(?:de\\s+)?(.+)$", Pattern.CASE_INSENSITIVE).matcher(linha);
        if (quantidadePrimeiro.find()) {
            return montarItem(quantidadePrimeiro.group(3), quantidadePrimeiro.group(1), quantidadePrimeiro.group(2));
        }

        Matcher produtoPrimeiro = Pattern.compile("^(.+?)\\s+([0-9]+(?:[\\.,][0-9]+)?)\\s*([A-Za-zÀ-ÿçÇãÃõÕéÉíÍóÓúÚüÜ]+)\\.?$", Pattern.CASE_INSENSITIVE).matcher(linha);
        if (produtoPrimeiro.find()) {
            return montarItem(produtoPrimeiro.group(1), produtoPrimeiro.group(2), produtoPrimeiro.group(3));
        }

        Matcher quantidadeSemUnidade = Pattern.compile("^([0-9]+(?:[\\.,][0-9]+)?)\\s+(?:de\\s+)?(.+)$", Pattern.CASE_INSENSITIVE).matcher(linha);
        if (quantidadeSemUnidade.find()) {
            return montarItem(quantidadeSemUnidade.group(2), quantidadeSemUnidade.group(1), null);
        }

        Matcher produtoSemUnidade = Pattern.compile("^(.+?)\\s+([0-9]+(?:[\\.,][0-9]+)?)\\.?$", Pattern.CASE_INSENSITIVE).matcher(linha);
        if (produtoSemUnidade.find()) {
            return montarItem(produtoSemUnidade.group(1), produtoSemUnidade.group(2), null);
        }

        return null;
    }

    private ItemInterpretado interpretarProdutoQuantidadeEmQualquerOrdem(String linha) {
        String frase = normalizarNumerosFalados(linha);
        Matcher quantidade = Pattern.compile("(?i)(?<![A-Z0-9])(\\d+(?:[\\.,]\\d+)?)\\s*(KG|KGS|QUILO|QUILOS|G|GR|GRAMAS|UN|UND|UNIDADES|CX|CAIXAS?|MC|MACOS?|SC|SACOS?)(?![A-Z0-9])").matcher(frase);
        if (!quantidade.find()) return null;
        String quantidadeTexto = quantidade.group(1);
        String unidadeTexto = quantidade.group(2);
        String produtoTexto = (frase.substring(0, quantidade.start()) + " " + frase.substring(quantidade.end()))
            .replaceAll("(?i)\\b(?:DE|DO|DA|DOS|DAS)\\b", " ")
            .replaceAll("[,;:.\\-–—]+", " ")
            .replaceAll("\\s+", " ").trim();
        if (produtoTexto.isEmpty()) return null;
        if (quantidade.find()) return null;
        return montarItem(produtoTexto, quantidadeTexto, unidadeTexto);
    }

    private List<ItemInterpretado> interpretarItensVoz(String fraseOriginal) {
        List<ItemInterpretado> encontrados = new ArrayList<>();
        String frase = normalizarNumerosFalados(fraseOriginal);
        List<String> nomes = new ArrayList<>(produtos);
        List<int[]> mencoes = new ArrayList<>();
        for (int indice = 0; indice < nomes.size(); indice++) {
            String nome = normalizarNomeProduto(nomes.get(indice));
            if (nome.isEmpty()) continue;
            Matcher matcher = Pattern.compile("(?<![A-Z0-9])" + Pattern.quote(nome) + "(?![A-Z0-9])").matcher(frase);
            while (matcher.find()) mencoes.add(new int[]{matcher.start(), matcher.end(), indice});
        }
        Collections.sort(mencoes, (a, b) -> {
            int inicio = Integer.compare(a[0], b[0]);
            return inicio != 0 ? inicio : Integer.compare((b[1] - b[0]), (a[1] - a[0]));
        });
        List<int[]> mencoesSemSobreposicao = new ArrayList<>();
        int fimCoberto = -1;
        for (int[] mencao : mencoes) {
            if (mencao[0] < fimCoberto) continue;
            mencoesSemSobreposicao.add(mencao);
            fimCoberto = mencao[1];
        }

        if (mencoesSemSobreposicao.size() > 1) {
            for (int indice = 0; indice < mencoesSemSobreposicao.size(); indice++) {
                int[] mencao = mencoesSemSobreposicao.get(indice);
                int fim = indice + 1 < mencoesSemSobreposicao.size()
                    ? mencoesSemSobreposicao.get(indice + 1)[0] : frase.length();
                String trecho = frase.substring(mencao[0], fim)
                    .replaceAll("(?i)\\s+(?:E|TAMBEM|DEPOIS|MAIS)\\s*$", "")
                    .replaceAll("[,;]+\\s*$", "")
                    .trim();
                ItemInterpretado item = interpretarLinhaPedido(trecho);
                if (item != null) encontrados.add(item);
            }
            return encontrados.size() == mencoesSemSobreposicao.size() ? encontrados : new ArrayList<>();
        }

        ItemInterpretado unico = interpretarLinhaPedido(frase);
        if (unico != null) encontrados.add(unico);
        return encontrados;
    }

    private ItemInterpretado interpretarComPadrao(String linha, String regex) {
        Matcher m = Pattern.compile(regex, Pattern.CASE_INSENSITIVE).matcher(linha);
        if (!m.find()) return null;
        return montarItem(m.group(1), m.group(2), m.group(3));
    }

    private ItemInterpretado montarItem(String produtoTexto, String medidaTexto, String unidadeTexto) {
        Double medida = numero(medidaTexto);
        String unidadeCodigo = unidadeTexto == null || unidadeTexto.trim().isEmpty()
            ? null : normalizarUnidade(unidadeTexto);
        String produtoNome = produtoCanonico(produtoTexto);
        if (unidadeCodigo == null && (unidadeTexto == null || unidadeTexto.trim().isEmpty()) && produtoNome != null) {
            unidadeCodigo = obterUnidadeProduto(produtoNome);
        }
        if (medida == null || medida <= 0 || unidadeCodigo == null || produtoNome == null) return null;
        return new ItemInterpretado(produtoNome, medida, unidadeCodigo);
    }

    private String limparLinhaPedido(String linha) {
        return linha
            .replace("•", " ")
            .replace("·", " ")
            .replace("●", " ")
            .replace("▪", " ")
            .replace("*", " ")
            .replace("_", " ")
            .replaceAll("^[\\s\\.\\-–—]+", "")
            .replaceAll("\\s+", " ")
            .trim();
    }

    private boolean deveIgnorarLinhaPedido(String linha) {
        String n = normalizarNomeProduto(linha);
        if (n.matches("^\\d{1,2}[\\/\\.\\-]\\d{1,2}[\\/\\.\\-]?\\d{0,4}$")) return true;
        if (n.startsWith("@")) return true;
        return n.contains("ENCAMINHADA")
            || n.startsWith("BOM DIA")
            || n.startsWith("RECEBIDO")
            || n.startsWith("PEDIDO")
            || n.startsWith("SOLICITACAO")
            || n.startsWith("OBS")
            || n.startsWith("FORNECEDOR")
            || n.startsWith("ENTREGAR")
            || n.startsWith("UND ")
            || n.startsWith("RECEBIDO POR");
    }

    private boolean pareceLinhaDeProduto(String linha) {
        String n = normalizarNomeProduto(linha);
        if (deveIgnorarLinhaPedido(linha)) return false;
        return n.matches(".*\\d+.*(KG|UND|UN|CX|CAIXA|CAIXAS|MC|MACO|MACOS|MÇ|SC|SACO|SACOS|PE|PES).*")
            || n.contains("=") || n.contains(" DE ");
    }

    private String normalizarUnidade(String texto) {
        String u = normalizarNomeProduto(texto).replace(".", "").trim();
        if (u.equals("KG") || u.equals("KGS") || u.startsWith("QUILO")) return "KG";
        if (u.equals("UN") || u.equals("UND") || u.startsWith("UNID") || u.equals("PE") || u.equals("PES")) return "UN";
        if (u.equals("CX") || u.startsWith("CAIX")) return "CX";
        if (u.equals("MC") || u.equals("MÇ") || u.equals("MARCO") || u.equals("MARCOS") || u.startsWith("MACO")) return "MC";
        if (u.equals("SC") || u.startsWith("SACO")) return "SC";
        return null;
    }

    private String produtoCanonico(String texto) {
        String n = normalizarNomeProduto(texto)
            .replaceAll("\\bDE\\b", " ")
            .replaceAll("\\bDA\\b", " ")
            .replaceAll("\\bDO\\b", " ")
            .replaceAll("\\bDAS\\b", " ")
            .replaceAll("\\bDOS\\b", " ")
            .replaceAll("\\bNATURAL\\b", " ")
            .replaceAll("\\bDESCASCATO\\b", " ")
            .replaceAll("\\bDESCASCADO\\b", " ")
            .replaceAll("\\s+", " ")
            .trim();

        Map<String, String> aliases = new HashMap<>();
        aliases.put("ABOBORA", "ABÓBORA");
        aliases.put("ABOBRA", "ABÓBORA");
        aliases.put("MACA", "MAÇÃ");
        aliases.put("MACA CX", "MAÇÃ");
        aliases.put("MELAO", "MELÃO");
        aliases.put("LIMAO", "LIMÃO");
        aliases.put("MAMAO", "MAMÃO");
        aliases.put("PIMENTAO", "PIMENTÃO");
        aliases.put("MANJERICAO", "MANJERICÃO");
        aliases.put("PIMENTINHA", "PIMENTA DE CHEIRO");
        aliases.put("CHEIRO VERDDE", "CHEIRO VERDE");
        aliases.put("REPOLHO BRANCO", "REPOLHO VERDE");
        aliases.put("ALHO DESCASCATO", "ALHO");
        aliases.put("ALHO DESCASCADO", "ALHO");
        aliases.put("MACAXEIRA NATURAL", "MACAXEIRA");

        if (aliases.containsKey(n)) return encontrarProdutoCatalogo(aliases.get(n));
        if (n.contains("PIMENTA CHEIRO")) return encontrarProdutoCatalogo("PIMENTA DE CHEIRO");
        if (n.contains("CHEIRO VERD")) return encontrarProdutoCatalogo("CHEIRO VERDE");
        if (n.contains("REPOLHO BRANCO")) return encontrarProdutoCatalogo("REPOLHO VERDE");

        String direto = encontrarProdutoCatalogo(n);
        if (direto != null) return direto;
        for (String p : produtos) {
            String pn = normalizarNomeProduto(p);
            if (n.length() >= 4 && (n.contains(pn) || pn.contains(n))) return p;
        }
        return null;
    }

    private String encontrarProdutoCatalogo(String nome) {
        String alvo = normalizarNomeProduto(nome);
        for (String p : produtos) {
            if (normalizarNomeProduto(p).equals(alvo)) return p;
        }
        return nome;
    }

    private void adicionarItem() {
        String nome = produto.getSelectedItem() == null ? "" : produto.getSelectedItem().toString().trim();
        Double medida = numero(peso.getText().toString());
        String valorDigitado = valor.getText().toString().trim();
        Double preco = valorDigitado.isEmpty() ? obterPrecoSalvo(nome) : numero(valorDigitado);
        boolean valorInformado = preco != null;
        if (nome.isEmpty() || medida == null || medida <= 0) {
            aviso("Informe o produto e " + rotuloMedida(unidade.getSelectedItem().toString()).toLowerCase() + " válidos."); return;
        }
        if (!valorDigitado.isEmpty() && (preco == null || preco < 0)) {
            aviso("Informe um valor unitário válido, como 22,50, ou deixe o campo vazio."); valor.requestFocus(); return;
        }
        if (!valorDigitado.isEmpty()) salvarPrecoProduto(nome, preco);
        itens.add(new ItemPedido(nome, medida, unidade.getSelectedItem().toString(), preco == null ? 0 : preco, valorInformado));
        peso.setText(""); valor.setText(""); peso.requestFocus();
        esconderTeclado();
        atualizarDicaValor();
        atualizarLista();
    }

    private void carregarProdutos() {
        String[] padrao = {"ABACAXI", "ABOBRINHA", "ABÓBORA", "ALFACE", "ALHO", "AÇAFRÃO",
            "BANANA PACOVAN", "BANANA PRATA", "BATATA DOCE", "BATATA INGLESA", "BETERRABA",
            "CANELA EM PÓ", "CEBOLA", "CENOURA", "CHEIRO VERDE", "CHIMICHURRI", "COUVE",
            "GERGELIM", "LARANJA", "MACAXEIRA", "MANGA", "MANJERICÃO", "MAÇÃ", "MELANCIA",
            "MELÃO", "PEPINO", "PIMENTA", "PIMENTA DE CHEIRO", "PIMENTA DO REINO", "PIMENTÃO",
            "REPOLHO ROXO", "REPOLHO VERDE", "TOMATE", "UVA PASSA", "LIMÃO", "ERVAS FINAS",
            "COLORAU", "MAMÃO"};
        Set<String> salvos = getSharedPreferences("catalogo_monteiro", MODE_PRIVATE).getStringSet("produtos", null);
        if (salvos == null || salvos.isEmpty())
            salvos = getSharedPreferences("catalogo", MODE_PRIVATE).getStringSet("produtos", null);
        produtos.clear();
        produtos.addAll(salvos == null ? Arrays.asList(padrao) : new ArrayList<>(salvos));
        ordenarProdutos();
    }

    private void sincronizarCatalogoMonteiro(CatalogoSyncCallback callback) {
        new Thread(() -> {
            HttpURLConnection conexao = null;
            try {
                conexao = (HttpURLConnection) new URL(MONTEIRO_PRODUCTS_URL).openConnection();
                conexao.setRequestMethod("GET");
                conexao.setConnectTimeout(8000);
                conexao.setReadTimeout(12000);
                conexao.setRequestProperty("Cache-Control", "no-cache");
                conexao.setRequestProperty("x-token", tokenSistema());
                int status = conexao.getResponseCode();
                if (status < 200 || status >= 300) throw new Exception("servidor respondeu " + status);
                JSONArray resposta = new JSONArray(new String(lerFluxo(conexao.getInputStream()), "UTF-8"));
                LinkedHashSet<String> nomes = new LinkedHashSet<>();
                for (int i = 0; i < resposta.length(); i++) {
                    JSONObject produtoRemoto = resposta.optJSONObject(i);
                    if (produtoRemoto == null) continue;
                    String nome = produtoRemoto.optString("name", "").trim();
                    if (!nome.isEmpty()) nomes.add(nome);
                }
                if (nomes.isEmpty()) throw new Exception("lista oficial vazia");
                Set<String> cache = new LinkedHashSet<>(nomes);
                getSharedPreferences("catalogo_monteiro", MODE_PRIVATE).edit().putStringSet("produtos", cache).commit();
                runOnUiThread(() -> {
                    aplicarCatalogoMonteiro(cache);
                    if (callback != null) callback.concluir(true, true);
                });
            } catch (Exception e) {
                boolean temCache = getSharedPreferences("catalogo_monteiro", MODE_PRIVATE).contains("produtos");
                runOnUiThread(() -> {
                    if (temCache) carregarProdutos();
                    if (callback != null) callback.concluir(temCache, false);
                });
            } finally {
                if (conexao != null) conexao.disconnect();
            }
        }).start();
    }

    private void aplicarCatalogoMonteiro(Set<String> nomes) {
        String selecionado = produto == null || produto.getSelectedItem() == null
            ? "" : produto.getSelectedItem().toString();
        produtos.clear();
        produtos.addAll(nomes);
        ordenarProdutos();
        if (produtosAdapter != null) {
            produtosAdapter.notifyDataSetChanged();
            int posicao = produtos.indexOf(selecionado);
            if (posicao >= 0 && produto != null) produto.setSelection(posicao);
        }
    }

    private void cadastrarNovoProduto() {
        EditText entrada = campo("Nome do novo produto", InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_CAP_CHARACTERS);
        Spinner unidadeNova = new Spinner(this);
        String[] opcoesUnidade = {"KG", "UN", "CX", "MC", "SC"};
        unidadeNova.setAdapter(new ArrayAdapter<>(this, android.R.layout.simple_spinner_dropdown_item, opcoesUnidade));
        unidadeNova.setBackground(fundoComBorda(Color.rgb(254, 240, 138), Color.rgb(202, 138, 4), 10));
        LinearLayout formulario = coluna(); formulario.setPadding(dp(18), dp(4), dp(18), 0);
        formulario.addView(entrada);
        formulario.addView(texto("Unidade de medida", 14, true));
        formulario.addView(unidadeNova, new LinearLayout.LayoutParams(-1, dp(52)));
        new AlertDialog.Builder(this)
            .setTitle("Cadastrar produto")
            .setView(formulario)
            .setNegativeButton("Cancelar", null)
            .setPositiveButton("Salvar", (dialog, which) -> {
                String nome = entrada.getText().toString().trim().toUpperCase(new Locale("pt", "BR"));
                if (nome.isEmpty()) { aviso("Digite o nome do produto."); return; }
                if (!produtos.contains(nome)) produtos.add(nome);
                salvarUnidadeProduto(nome, unidadeNova.getSelectedItem().toString());
                ordenarProdutos();
                getSharedPreferences("catalogo", MODE_PRIVATE).edit()
                    .putStringSet("produtos", new LinkedHashSet<>(produtos)).apply();
                if (produtosAdapter != null) produtosAdapter.notifyDataSetChanged();
                if (produto != null && produtos.contains(nome)) produto.setSelection(produtos.indexOf(nome));
                if (produto != null) atualizarDicaValor();
            }).show();
    }

    private void salvarProdutos() {
        ordenarProdutos();
        getSharedPreferences("catalogo", MODE_PRIVATE).edit()
            .putStringSet("produtos", new LinkedHashSet<>(produtos)).apply();
        if (produtosAdapter != null) produtosAdapter.notifyDataSetChanged();
    }

    private void gerenciarProdutos() {
        ScrollView scroll = new ScrollView(this);
        LinearLayout lista = coluna();
        lista.setPadding(dp(12), dp(6), dp(12), dp(6));
        scroll.addView(lista);
        for (String nome : new ArrayList<>(produtos)) {
            LinearLayout linha = new LinearLayout(this);
            linha.setGravity(Gravity.CENTER_VERTICAL);
            TextView nomeView = texto(nome, 15, false);
            linha.addView(nomeView, new LinearLayout.LayoutParams(0, dp(44), 1));
            Button editar = botao("Editar", Color.rgb(30, 64, 175));
            editar.setOnClickListener(v -> editarProdutoCatalogo(nome));
            linha.addView(editar, new LinearLayout.LayoutParams(dp(82), dp(40)));
            Button excluir = botao("×", Color.rgb(185, 28, 28));
            excluir.setOnClickListener(v -> confirmarExcluirProduto(nome));
            LinearLayout.LayoutParams excluirParams = new LinearLayout.LayoutParams(dp(46), dp(40));
            excluirParams.setMargins(dp(4), 0, 0, 0);
            linha.addView(excluir, excluirParams);
            lista.addView(linha);
        }
        new AlertDialog.Builder(this).setTitle("Produtos cadastrados (" + produtos.size() + ")")
            .setView(scroll).setPositiveButton("Fechar", null).show();
    }

    private void editarProdutoCatalogo(String antigo) {
        EditText entrada = campo("Nome do produto", InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_CAP_CHARACTERS);
        entrada.setText(antigo); entrada.selectAll();
        new AlertDialog.Builder(this).setTitle("Editar produto").setView(entrada)
            .setNegativeButton("Cancelar", null)
            .setPositiveButton("Salvar", (d, w) -> {
                String novo = entrada.getText().toString().trim().toUpperCase(new Locale("pt", "BR"));
                if (novo.isEmpty()) { aviso("Digite o nome do produto."); return; }
                int posicao = produtos.indexOf(antigo);
                if (posicao >= 0) produtos.set(posicao, novo);
                Double precoAntigo = obterPrecoSalvo(antigo);
                String unidadeAntiga = obterUnidadeProduto(antigo);
                if (precoAntigo != null && !antigo.equals(novo)) {
                    salvarPrecoProduto(novo, precoAntigo);
                    getSharedPreferences("precos_produtos", MODE_PRIVATE).edit().remove(antigo).apply();
                }
                if (!antigo.equals(novo)) {
                    salvarUnidadeProduto(novo, unidadeAntiga);
                    getSharedPreferences("unidades_produtos", MODE_PRIVATE).edit().remove(antigo).apply();
                }
                salvarProdutos(); aviso("Produto atualizado.");
            }).show();
    }

    private void confirmarExcluirProduto(String nome) {
        new AlertDialog.Builder(this).setTitle("Excluir produto?").setMessage(nome)
            .setNegativeButton("Cancelar", null)
            .setPositiveButton("Excluir", (d, w) -> {
                produtos.remove(nome);
                getSharedPreferences("precos_produtos", MODE_PRIVATE).edit().remove(nome).apply();
                getSharedPreferences("unidades_produtos", MODE_PRIVATE).edit().remove(nome).apply();
                salvarProdutos();
                if (produto != null) atualizarDicaValor();
                aviso("Produto excluído.");
            }).show();
    }

    private void atualizarLista() {
        listaItens.removeAllViews();
        if (itens.isEmpty()) {
            TextView vazio = texto("Nenhum produto adicionado.\nAdicione um produto para liberar o envio.", 14, false);
            vazio.setTextColor(COR_TEXTO_SUAVE);
            vazio.setPadding(dp(12), dp(12), dp(12), dp(12));
            vazio.setBackground(fundoArredondado(COR_CARD_ESCURO_2, 9));
            listaItens.addView(vazio);
        }
        double total = 0;
        for (int i = 0; i < itens.size(); i++) {
            ItemPedido item = itens.get(i); total += item.total();
            LinearLayout cartao = coluna();
            cartao.setPadding(dp(12), dp(10), dp(12), dp(10));
            cartao.setBackground(fundoArredondado(COR_CARD_ESCURO_2, 9));
            LinearLayout.LayoutParams cartaoParams = new LinearLayout.LayoutParams(-1, -2);
            cartaoParams.setMargins(0, dp(4), 0, dp(4));
            cartao.setLayoutParams(cartaoParams);
            String valorTexto = item.valorInformado ? moeda.format(item.valor) : "—";
            String totalItemTexto = item.valorInformado ? moeda.format(item.total()) : "—";
            if (item.novo) cartao.addView(rotuloNovoProduto());
            TextView detalhe = texto(item.produto + "\n" + rotuloMedida(item.unidade) + ": " + formatarNumero(item.peso) + " " + item.unidade + " × " + valorTexto + " = " + totalItemTexto, 14, false);
            detalhe.setTextColor(COR_TEXTO_CLARO);
            cartao.addView(detalhe, new LinearLayout.LayoutParams(-1, -2));
            LinearLayout acoes = new LinearLayout(this);
            acoes.setOrientation(LinearLayout.HORIZONTAL);
            acoes.setGravity(Gravity.CENTER_VERTICAL);
            Button editar = botao("Editar", Color.rgb(30, 64, 175));
            editar.setOnClickListener(v -> editarItem(item));
            LinearLayout.LayoutParams editarParams = new LinearLayout.LayoutParams(0, dp(42), 1);
            editarParams.setMargins(0, dp(6), dp(4), 0);
            acoes.addView(editar, editarParams);
            Button excluir = botao("Excluir", Color.rgb(185, 28, 28));
            excluir.setOnClickListener(v -> { itens.remove(item); atualizarLista(); });
            LinearLayout.LayoutParams excluirParams = new LinearLayout.LayoutParams(0, dp(42), 1);
            excluirParams.setMargins(dp(4), dp(6), 0, 0);
            acoes.addView(excluir, excluirParams);
            cartao.addView(acoes);
            listaItens.addView(cartao);
        }
        String rotuloProdutos = itens.size() == 1 ? "1 produto" : itens.size() + " produtos";
        totalText.setText(rotuloProdutos + "\nTotal: " + moeda.format(total));
        if (enviarSistemaButton != null) {
            enviarSistemaButton.setEnabled(!itens.isEmpty());
            enviarSistemaButton.setAlpha(itens.isEmpty() ? 0.55f : 1f);
        }
        agendarSalvarRascunho();
    }

    private void editarItem(ItemPedido item) {
        int produtoPos = produtos.indexOf(item.produto);
        if (produtoPos >= 0) produto.setSelection(produtoPos);
        peso.setText(formatarNumero(item.peso));
        valor.setText(item.valorInformado ? decimal(item.valor) : "");
        for (int i = 0; i < unidade.getCount(); i++)
            if (unidade.getItemAtPosition(i).toString().equals(item.unidade)) unidade.setSelection(i);
        itens.remove(item); atualizarLista(); peso.requestFocus();
        aviso("Altere os dados e toque em Adicionar produto.");
    }

    private void enviarTexto() {
        String nomeCliente = obterCliente();
        List<String> vazios = new ArrayList<>();
        if (nomeCliente.isEmpty()) vazios.add("cliente");
        if (data.getText().toString().trim().isEmpty()) vazios.add("data");
        if (itens.isEmpty()) vazios.add("produtos");
        if (!vazios.isEmpty()) {
            new AlertDialog.Builder(this)
                .setTitle("Deixar em branco?")
                .setMessage("Os seguintes campos estão vazios: " + android.text.TextUtils.join(", ", vazios) + ".\n\nDeseja continuar mesmo assim?")
                .setNegativeButton("Voltar e preencher", null)
                .setPositiveButton("Continuar em branco", (d, w) -> prepararEnvioNota(nomeCliente))
                .show();
            return;
        }
        prepararEnvioNota(nomeCliente);
    }

    private String obterCliente() {
        if (cliente.getSelectedItem() == null) return "";
        String selecionado = cliente.getSelectedItem().toString();
        return nomeClienteMaiusculo("OUTRO".equals(selecionado) ? clienteOutro.getText().toString() : selecionado);
    }

    private String nomeClienteMaiusculo(String nome) {
        return nome == null ? "" : nome.trim().toUpperCase(new Locale("pt", "BR"));
    }

    private void prepararEnvioNota(String nomeCliente) {
        definirStatusEnvio("Verificando se já existe uma nota para evitar duplicidade...", Color.rgb(37, 99, 235));
        enviarSistemaButton.setEnabled(false);
        enviarSistemaButton.setText("Verificando notas...");
        final List<ItemPedido> itensEnvio = new ArrayList<>(itens);
        final JSONObject body;
        try {
            body = criarPayload(pedidoId, nomeCliente, data.getText().toString().trim(), itensEnvio);
        }
        catch (Exception e) {
            restaurarBotaoEnvio();
            definirStatusEnvio("Não foi possível preparar a nota. Confira os campos e tente novamente.", Color.rgb(185, 28, 28));
            aviso("Não foi possível preparar a nota: " + e.getMessage()); return;
        }
        resolverUnificacao(body, enviarSistemaButton,
            noteId -> enviarNotaSistema(nomeCliente, body, itensEnvio, noteId),
            () -> {
                restaurarBotaoEnvio();
                definirStatusEnvio("Envio cancelado. A nota continua em edição.", COR_TEXTO_SUAVE);
            });
    }

    private void enviarNotaSistema(String nomeCliente, JSONObject body, List<ItemPedido> itensEnvio, String mergeIntoNoteId) {
        definirStatusEnvio("Enviando nota ao servidor...", Color.rgb(37, 99, 235));
        enviarSistemaButton.setEnabled(false);
        enviarSistemaButton.setText("Enviando...");
        try {
            body.put("merge_decided", true);
            body.put("merge_into_note_id", mergeIntoNoteId == null ? "" : mergeIntoNoteId);
        } catch (Exception e) {
            restaurarBotaoEnvio();
            definirStatusEnvio("Não foi possível iniciar o envio. A nota continua em edição.", Color.rgb(185, 28, 28));
            aviso("Não foi possível preparar a decisão de unificação: " + e.getMessage()); return;
        }
        new Thread(() -> {
            try {
                JSONObject resposta = postarNota(body);
                JSONObject submissao = resposta.optJSONObject("submission");
                if (submissao != null) body.put("server_submission", submissao);
                salvarNotaEnviada(body);
                runOnUiThread(() -> {
                    itens.removeAll(itensEnvio); atualizarLista(); pedidoId = UUID.randomUUID().toString();
                    peso.setText(""); valor.setText("");
                    limparRascunhoNota();
                    if (envioOrigemVoz) {
                        envioOrigemVoz = false;
                        limparRascunhoVoz();
                        String confirmacao = "Nota enviada ao ERP. Pode iniciar o próximo pedido.";
                        Toast.makeText(this, confirmacao, Toast.LENGTH_LONG).show();
                        iniciarSessaoVoz();
                        return;
                    }
                    definirStatusEnvio("Enviada ao sistema com sucesso.", Color.rgb(21, 128, 61));
                    new AlertDialog.Builder(this).setTitle("Nota enviada")
                        .setMessage("O pedido foi recebido pelo sistema e está disponível em Monteiro > Notas APP.\n\n"
                            + resumoSubmissao(submissao))
                        .setPositiveButton("OK", null).show();
                });
            } catch (Exception e) {
                salvarNotaPendente(body);
                String diagnostico = detalheFalhaEnvioNota(e);
                String orientacao = diagnostico.contains("servidor respondeu 401")
                    ? "\n\nO servidor recusou a autorização do aplicativo. A nota continua salva no celular; atualize a configuração do APK antes de tentar novamente."
                    : "\n\nConfira a conexão e tente reenviar em Notas pendentes. A nota continua salva no celular.";
                runOnUiThread(() -> {
                    envioOrigemVoz = false;
                    limparRascunhoVoz();
                    itens.removeAll(itensEnvio); atualizarLista(); pedidoId = UUID.randomUUID().toString();
                    peso.setText(""); valor.setText(""); atualizarBotaoPendentes();
                    limparRascunhoNota();
                    definirStatusEnvio("Pendente: salva neste aparelho para reenvio.", Color.rgb(180, 83, 9));
                    new AlertDialog.Builder(this).setTitle("Nota salva no celular")
                        .setMessage("O envio não foi concluído. A nota foi guardada em Notas pendentes de envio e não será perdida.\n\nDetalhe técnico: " + diagnostico + orientacao)
                        .setPositiveButton("OK", null).show();
                });
            } finally {
                runOnUiThread(this::restaurarBotaoEnvio);
            }
        }).start();
    }

    private void restaurarBotaoEnvio() {
        if (enviarSistemaButton == null || !"pedido".equals(telaAtual)) return;
        enviarSistemaButton.setText("Enviar nota para o sistema");
        enviarSistemaButton.setEnabled(!itens.isEmpty());
        enviarSistemaButton.setAlpha(itens.isEmpty() ? 0.55f : 1f);
    }

    private void resolverUnificacao(JSONObject nota, Button botao, DestinoUnificacaoCallback callback, Runnable cancelar) {
        new Thread(() -> {
            try {
                JSONObject resposta = buscarNotasMesmoDia(nota);
                JSONArray matches = resposta.optJSONArray("matches");
                runOnUiThread(() -> {
                    if (resposta.optBoolean("already_received") || matches == null || matches.length() == 0) {
                        callback.continuar(null);
                    } else {
                        mostrarOpcoesUnificacao(matches, callback, cancelar);
                    }
                });
            } catch (Exception erro) {
                runOnUiThread(() -> new AlertDialog.Builder(this)
                    .setTitle("Não foi possível verificar notas")
                    .setMessage("Não consegui consultar se já existe nota deste estabelecimento nesta data.\n\nDetalhe: "
                        + detalheFalhaEnvioNota(erro) + "\n\nDeseja enviar como uma nota separada?")
                    .setPositiveButton("Enviar separada", (d, w) -> callback.continuar(null))
                    .setNegativeButton("Cancelar", (d, w) -> cancelar.run())
                    .setOnCancelListener(d -> cancelar.run())
                    .show());
            }
        }).start();
    }

    private JSONObject buscarNotasMesmoDia(JSONObject nota) throws Exception {
        String query = "?client=" + URLEncoder.encode(nota.optString("client"), "UTF-8")
            + "&date=" + URLEncoder.encode(nota.optString("date"), "UTF-8")
            + "&external_id=" + URLEncoder.encode(nota.optString("external_id"), "UTF-8");
        HttpURLConnection conexao = null;
        try {
            conexao = (HttpURLConnection) new URL(APP_NOTES_MATCHES_URL + query).openConnection();
            conexao.setRequestMethod("GET");
            conexao.setConnectTimeout(12000);
            conexao.setReadTimeout(20000);
            conexao.setRequestProperty("Cache-Control", "no-cache");
            conexao.setRequestProperty("x-app-token", APP_NOTES_TOKEN);
            conexao.setRequestProperty("x-token", tokenSistema());
            int status = conexao.getResponseCode();
            String json = new String(lerFluxo(status >= 200 && status < 300
                ? conexao.getInputStream() : conexao.getErrorStream()), "UTF-8");
            if (status < 200 || status >= 300) throw new Exception("servidor respondeu " + status + ": " + json);
            return new JSONObject(json);
        } finally {
            if (conexao != null) conexao.disconnect();
        }
    }

    private void mostrarOpcoesUnificacao(JSONArray matches, DestinoUnificacaoCallback callback, Runnable cancelar) {
        if (matches.length() == 1) {
            JSONObject match = matches.optJSONObject(0);
            if (match == null) { callback.continuar(null); return; }
            String detail = nomeClienteMaiusculo(match.optString("client", "Estabelecimento")) + " · " + match.optString("note_date", "")
                + "\n" + resumoUltimoEnvio(match) + "\n" + match.optInt("item_count") + " produto(s)"
                + "\n\nDeseja adicionar os novos produtos a esta nota? O novo horário e remetente ficarão registrados.";
            new AlertDialog.Builder(this)
                .setTitle("Nota já existe neste dia")
                .setMessage(detail)
                .setPositiveButton("Unificar nesta nota", (d, w) -> callback.continuar(match.optString("id")))
                .setNegativeButton("Criar nota separada", (d, w) -> callback.continuar(null))
                .setNeutralButton("Cancelar", (d, w) -> cancelar.run())
                .setOnCancelListener(d -> cancelar.run())
                .show();
            return;
        }

        String[] opcoes = new String[matches.length()];
        for (int i = 0; i < matches.length(); i++) {
            JSONObject match = matches.optJSONObject(i);
            opcoes[i] = match == null ? "Nota existente" : resumoUltimoEnvio(match) + " · "
                + match.optInt("item_count") + " produto(s) · " + match.optString("status", "pendente");
        }
        new AlertDialog.Builder(this)
            .setTitle("Unificar com uma nota existente?")
            .setMessage("Escolha a nota que receberá os novos produtos. O horário e o remetente deste envio serão registrados.")
            .setItems(opcoes, (d, which) -> {
                JSONObject match = matches.optJSONObject(which);
                callback.continuar(match == null ? null : match.optString("id"));
            })
            .setNegativeButton("Criar nota separada", (d, w) -> callback.continuar(null))
            .setNeutralButton("Cancelar", (d, w) -> cancelar.run())
            .setOnCancelListener(d -> cancelar.run())
            .show();
    }

    private String resumoUltimoEnvio(JSONObject nota) {
        JSONArray submissions = nota.optJSONArray("submissions");
        JSONObject ultimo = submissions == null ? null : submissions.optJSONObject(submissions.length() - 1);
        if (ultimo == null) return "Horário anterior não informado";
        String recebido = ultimo.optString("received_at", "");
        int separador = recebido.indexOf('T');
        String hora = separador >= 0 && recebido.length() >= separador + 6
            ? recebido.substring(separador + 1, separador + 6) : recebido;
        String remetente = ultimo.optString("submitted_by_name", "").trim();
        if (remetente.isEmpty()) remetente = ultimo.optString("submitted_by_username", "").trim();
        if (remetente.isEmpty()) remetente = "remetente não identificado";
        return "Enviada às " + (hora.isEmpty() ? "--:--" : hora) + " por " + remetente;
    }

    private String resumoSubmissao(JSONObject submissao) {
        if (submissao == null) return "O servidor não retornou os dados de autoria deste envio.";
        String recebido = submissao.optString("received_at", "");
        int separador = recebido.indexOf('T');
        String hora = separador >= 0 && recebido.length() >= separador + 6
            ? recebido.substring(separador + 1, separador + 6) : recebido;
        String remetente = submissao.optString("submitted_by_name", "").trim();
        if (remetente.isEmpty()) remetente = submissao.optString("submitted_by_username", "").trim();
        if (remetente.isEmpty()) remetente = "remetente não identificado";
        return "Registrada às " + (hora.isEmpty() ? "--:--" : hora) + " por " + remetente + ".";
    }

    private JSONObject criarPayload(String id, String nomeCliente, String dataNota, List<ItemPedido> itensNota) throws Exception {
        JSONObject body = new JSONObject();
        body.put("external_id", id); body.put("client", nomeCliente); body.put("date", dataNota);
        JSONArray produtosJson = new JSONArray();
        for (ItemPedido item : itensNota) {
            JSONObject p = new JSONObject(); p.put("product", item.produto);
            p.put("weight", item.peso); p.put("unit", item.unidade);
            p.put("quantity", unidadeContavel(item.unidade) ? item.peso : JSONObject.NULL);
            p.put("is_new", item.novo);
            p.put("unit_price", item.valorInformado ? item.valor : JSONObject.NULL); produtosJson.put(p);
        }
        body.put("items", produtosJson); return body;
    }

    private boolean unidadeContavel(String unidade) {
        return "MC".equalsIgnoreCase(unidade) || "UN".equalsIgnoreCase(unidade)
            || "CX".equalsIgnoreCase(unidade) || "SC".equalsIgnoreCase(unidade);
    }

    private JSONObject postarNota(JSONObject body) throws Exception {
        HttpURLConnection conexao = null;
        try {
            byte[] conteudo = body.toString().getBytes("UTF-8");
            conexao = (HttpURLConnection) new URL(APP_NOTES_URL).openConnection();
            conexao.setRequestMethod("POST"); conexao.setDoOutput(true);
            conexao.setConnectTimeout(12000); conexao.setReadTimeout(30000);
            conexao.setRequestProperty("Content-Type", "application/json; charset=UTF-8");
            conexao.setRequestProperty("x-app-token", APP_NOTES_TOKEN);
            conexao.setRequestProperty("x-token", tokenSistema());
            conexao.setFixedLengthStreamingMode(conteudo.length);
            try (java.io.OutputStream saida = conexao.getOutputStream()) { saida.write(conteudo); }
            int status = conexao.getResponseCode();
            if (status < 200 || status >= 300) {
                String detalhe;
                try { detalhe = new String(lerFluxo(conexao.getErrorStream()), "UTF-8"); }
                catch (Exception e) { detalhe = "erro " + status; }
                throw new Exception("servidor respondeu " + status + ": " + detalhe);
            }
            String resposta = new String(lerFluxo(conexao.getInputStream()), "UTF-8");
            return resposta.trim().isEmpty() ? new JSONObject() : new JSONObject(resposta);
        } finally { if (conexao != null) conexao.disconnect(); }
    }

    private String detalheFalhaEnvioNota(Exception erro) {
        String detalhe = erro == null ? "Erro sem detalhe retornado." : erro.getMessage();
        if (detalhe == null || detalhe.trim().isEmpty()) detalhe = "Erro sem detalhe retornado.";
        detalhe = detalhe.trim();
        return detalhe.length() > 280 ? detalhe.substring(0, 280) + "…" : detalhe;
    }

    private synchronized JSONArray lerNotasPendentes() {
        try { return new JSONArray(getSharedPreferences("notas_offline", MODE_PRIVATE).getString("fila", "[]")); }
        catch (Exception e) { return new JSONArray(); }
    }

    private synchronized void salvarNotaPendente(JSONObject nota) {
        JSONArray fila = lerNotasPendentes();
        String id = nota.optString("external_id");
        for (int i = 0; i < fila.length(); i++) if (id.equals(fila.optJSONObject(i).optString("external_id"))) return;
        fila.put(nota); getSharedPreferences("notas_offline", MODE_PRIVATE).edit().putString("fila", fila.toString()).commit();
    }

    private synchronized void atualizarNotaPendente(JSONObject nota) {
        JSONArray fila = lerNotasPendentes(), atualizada = new JSONArray();
        String id = nota.optString("external_id");
        boolean substituida = false;
        for (int i = 0; i < fila.length(); i++) {
            JSONObject item = fila.optJSONObject(i);
            if (item == null) continue;
            if (id.equals(item.optString("external_id"))) {
                atualizada.put(nota);
                substituida = true;
            } else atualizada.put(item);
        }
        if (!substituida) atualizada.put(nota);
        getSharedPreferences("notas_offline", MODE_PRIVATE).edit().putString("fila", atualizada.toString()).commit();
    }

    private synchronized void removerNotaPendente(String id) {
        JSONArray antiga = lerNotasPendentes(), nova = new JSONArray();
        for (int i = 0; i < antiga.length(); i++) {
            JSONObject nota = antiga.optJSONObject(i);
            if (nota != null && !id.equals(nota.optString("external_id"))) nova.put(nota);
        }
        getSharedPreferences("notas_offline", MODE_PRIVATE).edit().putString("fila", nova.toString()).commit();
    }

    private void atualizarBotaoPendentes() {
        if (pendentesButton == null) return;
        int total = lerNotasPendentes().length();
        pendentesButton.setText(total == 0 ? "Notas pendentes de envio" : "Notas pendentes de envio (" + total + ")");
        pendentesButton.setBackground(fundoArredondado(total == 0 ? Color.rgb(75, 85, 99) : Color.rgb(180, 83, 9), 9));
    }

    private void mostrarNotasPendentes() {
        JSONArray fila = lerNotasPendentes();
        if (fila.length() == 0) { aviso("Não há notas pendentes de envio."); return; }
        ScrollView scroll = new ScrollView(this); LinearLayout lista = coluna(); lista.setPadding(dp(12), dp(6), dp(12), dp(6)); scroll.addView(lista);
        for (int i = 0; i < fila.length(); i++) {
            JSONObject nota = fila.optJSONObject(i); if (nota == null) continue;
            String id = nota.optString("external_id");
            LinearLayout cartao = coluna(); cartao.setPadding(dp(10), dp(8), dp(10), dp(8));
            cartao.setBackground(fundoArredondado(Color.rgb(255, 247, 237), 8));
            cartao.addView(texto(nomeClienteMaiusculo(nota.optString("client", "Cliente em branco")) + " — " + nota.optString("date") + "\n" + nota.optJSONArray("items").length() + " produto(s)", 15, true));
            LinearLayout acoes = new LinearLayout(this); acoes.setOrientation(LinearLayout.HORIZONTAL);
            Button enviar = botao("Enviar agora", Color.rgb(18, 140, 126));
            enviar.setOnClickListener(v -> reenviarNotaPendente(nota, enviar));
            acoes.addView(enviar, new LinearLayout.LayoutParams(0, dp(44), 1));
            Button excluir = botao("Excluir", Color.rgb(185, 28, 28));
            excluir.setOnClickListener(v -> new AlertDialog.Builder(this).setTitle("Excluir nota pendente?")
                .setMessage("Esta ação remove a cópia salva no celular.").setNegativeButton("Cancelar", null)
                .setPositiveButton("Excluir", (d, w) -> { removerNotaPendente(id); atualizarBotaoPendentes(); mostrarNotasPendentes(); }).show());
            LinearLayout.LayoutParams ep = new LinearLayout.LayoutParams(0, dp(44), 1); ep.setMargins(dp(6), 0, 0, 0); acoes.addView(excluir, ep);
            cartao.addView(acoes); LinearLayout.LayoutParams cp = new LinearLayout.LayoutParams(-1, -2); cp.setMargins(0, dp(4), 0, dp(4)); lista.addView(cartao, cp);
        }
        new AlertDialog.Builder(this).setTitle("Notas pendentes de envio").setView(scroll).setPositiveButton("Fechar", null).show();
    }

    private void reenviarNotaPendente(JSONObject nota, Button botaoEnviar) {
        botaoEnviar.setEnabled(false); botaoEnviar.setText("Enviando...");
        if (nota.optBoolean("merge_decided", false)) {
            executarReenvioNotaPendente(nota, botaoEnviar);
            return;
        }
        botaoEnviar.setText("Verificando notas...");
        resolverUnificacao(nota, botaoEnviar, noteId -> {
            try {
                nota.put("merge_decided", true);
                nota.put("merge_into_note_id", noteId == null ? "" : noteId);
                atualizarNotaPendente(nota);
                executarReenvioNotaPendente(nota, botaoEnviar);
            } catch (Exception e) {
                botaoEnviar.setEnabled(true); botaoEnviar.setText("Enviar agora");
                aviso("Não foi possível registrar a decisão de unificação: " + e.getMessage());
            }
        }, () -> { botaoEnviar.setEnabled(true); botaoEnviar.setText("Enviar agora"); });
    }

    private void executarReenvioNotaPendente(JSONObject nota, Button botaoEnviar) {
        botaoEnviar.setEnabled(false); botaoEnviar.setText("Enviando...");
        new Thread(() -> {
            try {
                JSONObject resposta = postarNota(nota);
                JSONObject submissao = resposta.optJSONObject("submission");
                if (submissao != null) nota.put("server_submission", submissao);
                salvarNotaEnviada(nota); removerNotaPendente(nota.optString("external_id"));
                runOnUiThread(() -> { atualizarBotaoPendentes(); aviso("Nota enviada com sucesso. " + resumoSubmissao(submissao)); });
            } catch (Exception e) {
                String diagnostico = detalheFalhaEnvioNota(e);
                String orientacao = diagnostico.contains("servidor respondeu 401")
                    ? "\n\nO servidor recusou a autorização do APK. A nota não foi excluída; é necessário corrigir a configuração de acesso do aplicativo."
                    : "\n\nA nota continua salva no celular e pode ser reenviada depois.";
                runOnUiThread(() -> new AlertDialog.Builder(this)
                    .setTitle("Reenvio não concluído")
                    .setMessage("Detalhe técnico: " + diagnostico + orientacao)
                    .setPositiveButton("OK", null)
                    .show());
            } finally { runOnUiThread(() -> { botaoEnviar.setEnabled(true); botaoEnviar.setText("Enviar agora"); }); }
        }).start();
    }

    private synchronized JSONArray lerNotasEnviadas() {
        try { return new JSONArray(getSharedPreferences("notas_enviadas", MODE_PRIVATE).getString("lista", "[]")); }
        catch (Exception e) { return new JSONArray(); }
    }

    private synchronized void salvarNotaEnviada(JSONObject notaOriginal) {
        try {
            JSONObject nota = new JSONObject(notaOriginal.toString());
            nota.put("client", nomeClienteMaiusculo(nota.optString("client", "")));
            nota.put("sent_at", new SimpleDateFormat("dd/MM/yyyy HH:mm", new Locale("pt", "BR")).format(Calendar.getInstance().getTime()));
            String id = nota.optString("external_id");
            JSONArray antigas = lerNotasEnviadas(), novas = new JSONArray();
            novas.put(nota);
            for (int i = 0; i < antigas.length() && novas.length() < 100; i++) {
                JSONObject n = antigas.optJSONObject(i);
                if (n != null && !id.equals(n.optString("external_id"))) novas.put(n);
            }
            getSharedPreferences("notas_enviadas", MODE_PRIVATE).edit().putString("lista", novas.toString()).commit();
        } catch (Exception ignored) { }
    }

    private void mostrarNotasEnviadas() {
        JSONArray notas = lerNotasEnviadas();
        ScrollView scroll = new ScrollView(this);
        LinearLayout lista = coluna();
        lista.setPadding(dp(12), dp(6), dp(12), dp(6));
        scroll.addView(lista);
        if (notas.length() == 0) lista.addView(texto("Nenhuma nota enviada salva neste celular.", 15, false));
        for (int i = 0; i < notas.length(); i++) {
            JSONObject nota = notas.optJSONObject(i); if (nota == null) continue;
            LinearLayout cartao = coluna();
            cartao.setPadding(dp(12), dp(10), dp(12), dp(10));
            cartao.setBackground(fundoArredondado(Color.rgb(240, 253, 244), 10));
            LinearLayout.LayoutParams cp = new LinearLayout.LayoutParams(-1, -2);
            cp.setMargins(0, dp(4), 0, dp(6));
            JSONArray items = nota.optJSONArray("items");
            int totalItens = items == null ? 0 : items.length();
            cartao.addView(texto(nomeClienteMaiusculo(nota.optString("client", "Cliente em branco")), 16, true));
            cartao.addView(texto("Data: " + nota.optString("date", "-") + " | Enviada: " + nota.optString("sent_at", "-") + "\n" + totalItens + " produto(s)", 13, false));
            LinearLayout acoes = new LinearLayout(this);
            acoes.setOrientation(LinearLayout.HORIZONTAL);
            Button recibo = botao("Emitir recibo", Color.rgb(21, 128, 61));
            recibo.setOnClickListener(v -> mostrarReciboNota(nota));
            acoes.addView(recibo, new LinearLayout.LayoutParams(0, dp(44), 1));
            Button whats = botao("WhatsApp", Color.rgb(18, 140, 126));
            whats.setOnClickListener(v -> enviarReciboWhatsApp(nota));
            LinearLayout.LayoutParams wp = new LinearLayout.LayoutParams(0, dp(44), 1);
            wp.setMargins(dp(6), 0, 0, 0);
            acoes.addView(whats, wp);
            cartao.addView(acoes);
            lista.addView(cartao, cp);
        }
        new AlertDialog.Builder(this).setTitle("Notas enviadas").setView(scroll).setPositiveButton("Fechar", null).show();
    }

    private void mostrarReciboNota(JSONObject nota) {
        String recibo = criarReciboNota(nota);
        ScrollView scroll = new ScrollView(this);
        TextView textoRecibo = texto(recibo, 14, false);
        textoRecibo.setTextIsSelectable(true);
        textoRecibo.setPadding(dp(12), dp(10), dp(12), dp(10));
        scroll.addView(textoRecibo);
        new AlertDialog.Builder(this)
            .setTitle("Recibo da nota")
            .setView(scroll)
            .setNegativeButton("Fechar", null)
            .setPositiveButton("Enviar WhatsApp", (d, w) -> enviarReciboWhatsApp(nota))
            .show();
    }

    private String criarReciboNota(JSONObject nota) {
        StringBuilder r = new StringBuilder();
        r.append("RECIBO DE PEDIDO\n");
        r.append("Menina dos Raios Ltda - Monteiro\n\n");
        r.append("Cliente: ").append(nomeClienteMaiusculo(nota.optString("client", "Sem cliente"))).append('\n');
        r.append("Data do pedido: ").append(nota.optString("date", "-")).append('\n');
        r.append("Enviado em: ").append(nota.optString("sent_at", "-")).append('\n');
        r.append("Nota APP: ").append(nota.optString("external_id", "-")).append("\n\n");
        r.append("PRODUTOS\n");
        JSONArray items = nota.optJSONArray("items");
        double total = 0;
        if (items != null) {
            for (int i = 0; i < items.length(); i++) {
                JSONObject item = items.optJSONObject(i);
                if (item == null) continue;
                double medida = item.optDouble("weight", 0);
                String unidadeItem = item.optString("unit", "");
                boolean temPreco = !item.isNull("unit_price");
                double preco = temPreco ? item.optDouble("unit_price", 0) : 0;
                double subtotal = medida * preco;
                if (temPreco) total += subtotal;
                r.append(i + 1).append(". ").append(item.optString("product", "Produto")).append('\n');
                r.append("   ").append(rotuloMedida(unidadeItem)).append(": ").append(formatarNumero(medida)).append(' ').append(unidadeItem).append('\n');
                r.append("   Valor unitario: ").append(temPreco ? moeda.format(preco) : "Nao informado").append('\n');
                r.append("   Subtotal: ").append(temPreco ? moeda.format(subtotal) : "-").append("\n\n");
            }
        }
        r.append("TOTAL INFORMADO: ").append(moeda.format(total)).append("\n\n");
        r.append("Este recibo comprova o registro do pedido recebido pelo aplicativo interno e nao substitui documento fiscal.");
        return r.toString();
    }

    private void enviarReciboWhatsApp(JSONObject nota) {
        String recibo = criarReciboNota(nota);
        Intent send = new Intent(Intent.ACTION_SEND);
        send.setType("text/plain");
        send.putExtra(Intent.EXTRA_TEXT, recibo);
        if (appInstalado("com.whatsapp")) send.setPackage("com.whatsapp");
        else if (appInstalado("com.whatsapp.w4b")) send.setPackage("com.whatsapp.w4b");
        try { startActivity(send); }
        catch (ActivityNotFoundException e) { startActivity(Intent.createChooser(send, "Enviar recibo")); }
    }

    private void abrirCentralNotificacoes(String abaInicial) {
        if (!adminNotificacoes()) { aviso("Central de notificações disponível somente para administradores."); return; }
        temaEscuroAtivo=true; telaAtual="central_notificacoes"; ScrollView scroll=new ScrollView(this);scroll.setBackgroundColor(COR_FUNDO_ESCURO);
        LinearLayout raiz=coluna();raiz.setPadding(dp(16),dp(14),dp(16),dp(26));scroll.addView(raiz);
        adicionarCabecalhoModulo(raiz,"Central de notificações","Calendário e cobranças · acesso somente admin.");
        LinearLayout abas=new LinearLayout(this);abas.setOrientation(LinearLayout.HORIZONTAL);Button calendario=botao("▦  Calendário",Color.rgb(21,101,52)), novoTempo=botao("＄  Novo Tempo",Color.WHITE);novoTempo.setTextColor(Color.rgb(21,101,52));
        abas.addView(calendario,new LinearLayout.LayoutParams(0,dp(48),1));LinearLayout.LayoutParams ntp=new LinearLayout.LayoutParams(0,dp(48),1);ntp.setMargins(dp(6),0,0,0);abas.addView(novoTempo,ntp);raiz.addView(abas);
        TextView permissao=texto("",13,true);permissao.setPadding(dp(12),dp(10),dp(12),dp(10));raiz.addView(permissao);
        TextView horarios=texto("",13,true);horarios.setPadding(dp(14),dp(12),dp(14),dp(12));horarios.setBackground(fundoComBorda(Color.rgb(240,248,242),Color.rgb(205,225,209),12));LinearLayout.LayoutParams horariosParams=new LinearLayout.LayoutParams(-1,-2);horariosParams.setMargins(0,dp(8),0,dp(8));raiz.addView(horarios,horariosParams);
        boolean[] mostrarPagos={false};
        LinearLayout filtroCobrancas=new LinearLayout(this);filtroCobrancas.setOrientation(LinearLayout.HORIZONTAL);Button pendentesTab=botao("Pendentes",Color.rgb(21,101,52)),pagosTab=botao("Pagos",Color.WHITE);pagosTab.setTextColor(Color.rgb(21,101,52));filtroCobrancas.addView(pendentesTab,new LinearLayout.LayoutParams(0,dp(44),1));LinearLayout.LayoutParams pagosTabParams=new LinearLayout.LayoutParams(0,dp(44),1);pagosTabParams.setMargins(dp(6),0,0,0);filtroCobrancas.addView(pagosTab,pagosTabParams);raiz.addView(filtroCobrancas);filtroCobrancas.setVisibility(View.GONE);
        LinearLayout resumoCobrancas=coluna();raiz.addView(resumoCobrancas);resumoCobrancas.setVisibility(View.GONE);
        LinearLayout lista=coluna();raiz.addView(lista);
        final String[] abaSelecionada={abaInicial}; Runnable[] carregar={null};
        Runnable mostrarPermissao=()->{NotificationManager nm=(NotificationManager)getSystemService(Context.NOTIFICATION_SERVICE);boolean ativa=nm!=null&&nm.areNotificationsEnabled();if(Build.VERSION.SDK_INT>=33&&checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)!=PackageManager.PERMISSION_GRANTED)ativa=false;permissao.setText("Notificações do Android: "+(ativa?"permitidas":"toque aqui para ativar")+"\nCalendário: "+CalendarNotificationReceiver.estadoUltimaVerificacao(this)+"\nNovo Tempo: "+NewTempoCollectionReceiver.estadoUltimaVerificacao(this));permissao.setBackground(fundoComBorda(ativa?Color.rgb(220,252,231):Color.rgb(255,237,213),ativa?Color.rgb(22,163,74):Color.rgb(234,88,12),10));permissao.setOnClickListener(v->{if(Build.VERSION.SDK_INT>=33&&checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)!=PackageManager.PERMISSION_GRANTED)requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS},410);else abrirConfiguracoesNotificacoes();});};
        carregar[0]=()->{mostrarPermissao.run();lista.removeAllViews();if("calendario".equals(abaSelecionada[0])){resumoCobrancas.setVisibility(View.GONE);horarios.setText("▦  Lembretes do calendário\n09:00  ·  13:00  ·  17:00  ·  21:00");filtroCobrancas.setVisibility(View.GONE);calendario.setBackground(fundoArredondado(Color.rgb(21,101,52),9));calendario.setTextColor(Color.WHITE);novoTempo.setBackground(fundoComBorda(Color.WHITE,Color.rgb(216,227,220),9));novoTempo.setTextColor(Color.rgb(21,101,52));TextView st=texto("Carregando eventos...",13,false);lista.addView(st);new Thread(()->{try{JSONArray ev=baixarEventosCalendario();runOnUiThread(()->{lista.removeAllViews();if(ev.length()==0)lista.addView(cardLeitura("Tudo em dia","Nenhum aviso pendente no calendário.","Confira novamente mais tarde.","",Color.rgb(220,252,231)));for(int i=0;i<ev.length();i++){JSONObject e=ev.optJSONObject(i);if(e!=null)lista.addView(cardLeitura(e.optString("title","Lembrete"),formatarDataIso(e.optString("due_date"))+" · "+(e.optInt("days_left")==0?"Hoje":"em "+e.optInt("days_left")+" dia(s)"),e.optString("details",""),"",Color.rgb(239,246,255)));}Button testar=botao("Testar aviso do calendário",Color.rgb(21,101,52));lista.addView(testar);testar.setOnClickListener(v->aviso(CalendarNotificationReceiver.testarNotificacao(this)));});}catch(Exception e){runOnUiThread(()->{lista.removeAllViews();lista.addView(cardLeitura("Calendário indisponível",mensagemErroSimples(e),"Verifique o acesso e tente atualizar.","",Color.rgb(255,237,213)));});}}).start();}
            else{resumoCobrancas.setVisibility(View.VISIBLE);horarios.setText("＄  Lembretes Novo Tempo\n08:00  ·  12:00  ·  16:00  ·  20:00\nSomente notas entregues há mais de 24 horas; acesso admin.");filtroCobrancas.setVisibility(View.VISIBLE);pendentesTab.setBackground(fundoArredondado(mostrarPagos[0]?Color.WHITE:Color.rgb(21,101,52),9));pendentesTab.setTextColor(mostrarPagos[0]?Color.rgb(21,101,52):Color.WHITE);pagosTab.setBackground(fundoArredondado(mostrarPagos[0]?Color.rgb(21,101,52):Color.WHITE,9));pagosTab.setTextColor(mostrarPagos[0]?Color.WHITE:Color.rgb(21,101,52));calendario.setBackground(fundoComBorda(Color.WHITE,Color.rgb(216,227,220),9));calendario.setTextColor(Color.rgb(21,101,52));novoTempo.setBackground(fundoArredondado(Color.rgb(21,101,52),9));novoTempo.setTextColor(Color.WHITE);TextView st=texto("Carregando cobranças Novo Tempo…",13,false);lista.addView(st);new Thread(()->{try{JSONArray rows=buscarArrayApi("/api/mobile/new-tempo/collections");runOnUiThread(()->{lista.removeAllViews();int quantidade=0,totalPendentes=0,aguardando24=0,aptasAviso=0,totalPagas=0;for(int i=0;i<rows.length();i++){JSONObject item=rows.optJSONObject(i);if(item==null)continue;boolean pago="pago".equalsIgnoreCase(item.optString("status"));if(pago){totalPagas++;continue;}totalPendentes++;if(!item.optBoolean("delivered",false)||item.optInt("hours_pending")<24)aguardando24++;else aptasAviso++;}pendentesTab.setText("Pendentes ("+totalPendentes+")");pagosTab.setText("Pagos ("+totalPagas+")");resumoCobrancas.removeAllViews();resumoCobrancas.addView(linhaKpis(cardIndicador("Pendentes",String.valueOf(totalPendentes),"Notas ainda em aberto",Color.rgb(21,101,52)),cardIndicador("Aguardando 24h",String.valueOf(aguardando24),"Desde a entrega",Color.rgb(202,138,4))));resumoCobrancas.addView(linhaKpis(cardIndicador("Prontas para aviso",String.valueOf(aptasAviso),"Entregues há pelo menos 24h",Color.rgb(37,99,235)),cardIndicador("Pagas",String.valueOf(totalPagas),"Baixadas no sistema",Color.rgb(22,163,74))));for(int i=0;i<rows.length();i++){JSONObject item=rows.optJSONObject(i);if(item==null)continue;boolean pago="pago".equalsIgnoreCase(item.optString("status"));if(pago!=mostrarPagos[0])continue;quantidade++;String age=item.optBoolean("delivered",false)?"Entregue · "+item.optInt("hours_pending")+"h":"Aguardando entrega";LinearLayout card=(LinearLayout)cardLeitura(item.optString("client","Novo Tempo"),"NF "+item.optString("nf_number","—")+" · "+dataBR(item.optString("sale_date")),moeda.format(item.optDouble("total",0))+" · "+age,"Próximo aviso: "+formatarDataIsoHora(item.optString("next_alert_at")),pago?Color.rgb(220,252,231):Color.rgb(255,247,237));if(!pago){Button pagoBtn=botao("✓  Marcar como pago",Color.rgb(21,101,52));card.addView(pagoBtn);JSONObject copia=item;pagoBtn.setOnClickListener(v->{new Thread(()->{try{JSONObject body=new JSONObject();body.put("company_key",copia.optString("company_key"));body.put("status","pago");enviarObjetoApi("/api/mobile/new-tempo/collections/"+copia.optString("id"),"PUT",body);runOnUiThread(()->{aviso("Cobrança marcada como paga.");carregar[0].run();});}catch(Exception ex){runOnUiThread(()->aviso("Não foi possível atualizar: "+mensagemErroSimples(ex)));}}).start();});}lista.addView(card);}if(quantidade==0)lista.addView(cardLeitura(mostrarPagos[0]?"Nenhuma venda paga":"Nenhuma cobrança pendente",mostrarPagos[0]?"As vendas marcadas como pagas aparecerão aqui.":"As notas Novo Tempo em aberto aparecerão aqui.","Somente administradores recebem os avisos.","",Color.rgb(220,252,231)));});}catch(Exception e){runOnUiThread(()->{lista.removeAllViews();lista.addView(cardLeitura("Cobranças indisponíveis",mensagemErroSimples(e),"Tente atualizar quando o ERP estiver acessível.","",Color.rgb(255,237,213)));});}}).start();}};
        calendario.setOnClickListener(v->{abaSelecionada[0]="calendario";carregar[0].run();});novoTempo.setOnClickListener(v->{abaSelecionada[0]="novo_tempo";carregar[0].run();});
        pendentesTab.setOnClickListener(v->{mostrarPagos[0]=false;carregar[0].run();});pagosTab.setOnClickListener(v->{mostrarPagos[0]=true;carregar[0].run();});
        Button atualizar=botao("⟳  Atualizar",Color.rgb(21,101,52));raiz.addView(atualizar);atualizar.setOnClickListener(v->carregar[0].run());
        Button testeNovo=botao("Testar aviso Novo Tempo",Color.rgb(71,85,105));raiz.addView(testeNovo);testeNovo.setOnClickListener(v->aviso(NewTempoCollectionReceiver.testarNotificacao(this)));
        setContentView(scroll);carregar[0].run();
    }

    private String formatarDataIsoHora(String iso) { if(iso==null||iso.trim().isEmpty())return "Aguardando 24h";try{String s=iso.replace('T',' ');return s.length()>=16?dataBR(s.substring(0,10))+" às "+s.substring(11,16):s;}catch(Exception e){return iso;} }

    private void abrirCalendarioNotificacoes() {
        if (!adminNotificacoes()) { aviso("Notificações disponíveis somente para administradores."); return; }
        aviso("Carregando notificações...");
        new Thread(() -> {
            try {
                JSONArray eventos = baixarEventosCalendario();
                runOnUiThread(() -> mostrarCalendarioNotificacoes(eventos));
            } catch (Exception e) {
                runOnUiThread(() -> aviso("Não foi possível carregar o calendário: " + e.getMessage()));
            }
        }).start();
    }

    private JSONArray baixarEventosCalendario() throws Exception {
        if (!adminNotificacoes()) throw new Exception("Acesso restrito a administradores.");
        HttpURLConnection conexao = null;
        try {
            conexao = (HttpURLConnection) new URL(APP_CALENDAR_URL).openConnection();
            conexao.setRequestMethod("GET");
            conexao.setConnectTimeout(12000);
            conexao.setReadTimeout(30000);
            conexao.setRequestProperty("Cache-Control", "no-cache");
            conexao.setRequestProperty("x-token", tokenSistema());
            int status = conexao.getResponseCode();
            if (status < 200 || status >= 300) throw new Exception("servidor respondeu " + status);
            String json = new String(lerFluxo(conexao.getInputStream()), "UTF-8");
            return new JSONObject(json).optJSONArray("events") == null ? new JSONArray() : new JSONObject(json).optJSONArray("events");
        } finally { if (conexao != null) conexao.disconnect(); }
    }

    private void mostrarCalendarioNotificacoes(JSONArray eventos) {
        if (!adminNotificacoes()) return;
        ScrollView scroll = new ScrollView(this);
        LinearLayout lista = coluna();
        lista.setPadding(dp(12), dp(6), dp(12), dp(6));
        scroll.addView(lista);
        TextView estadoNotificacao = texto(CalendarNotificationReceiver.estadoUltimaVerificacao(this), 12, false);
        estadoNotificacao.setPadding(dp(10), dp(8), dp(10), dp(8));
        lista.addView(estadoNotificacao);
        if (Build.VERSION.SDK_INT >= 31) {
            AlarmManager alarm = (AlarmManager) getSystemService(Context.ALARM_SERVICE);
            if (alarm != null && !alarm.canScheduleExactAlarms()) {
                Button horarioExato = botao("Permitir horários exatos", Color.rgb(21, 101, 52));
                lista.addView(horarioExato);
                horarioExato.setOnClickListener(v -> abrirConfiguracoesAlarmesExatos());
            }
        }
        if (eventos.length() == 0) {
            lista.addView(texto("Nenhuma notificação pendente para os próximos dias.", 15, false));
        }
        for (int i = 0; i < eventos.length(); i++) {
            JSONObject e = eventos.optJSONObject(i);
            if (e == null) continue;
            LinearLayout cartao = coluna();
            cartao.setPadding(dp(12), dp(10), dp(12), dp(10));
            cartao.setBackground(fundoArredondado(Color.rgb(239, 246, 255), 10));
            LinearLayout.LayoutParams cp = new LinearLayout.LayoutParams(-1, -2);
            cp.setMargins(0, dp(4), 0, dp(6));
            int dias = e.optInt("days_left", 0);
            String quando = dias == 0 ? "Hoje" : "Faltam " + dias + " dia(s)";
            cartao.addView(texto(e.optString("title", "Notificação"), 16, true));
            cartao.addView(texto("Data: " + formatarDataIso(e.optString("due_date")) + " • " + quando, 13, false));
            String detalhes = e.optString("details", "").trim();
            if (!detalhes.isEmpty()) cartao.addView(texto(detalhes, 14, false));
            lista.addView(cartao, cp);
        }
        new AlertDialog.Builder(this)
            .setTitle("Calendário de notificações")
            .setView(scroll)
            .setPositiveButton("Testar notificação", (dialog, which) -> {
                String resultado = CalendarNotificationReceiver.testarNotificacao(this);
                estadoNotificacao.setText(resultado);
                aviso(resultado);
            })
            .setNegativeButton("Fechar", null)
            .show();
    }

    private String formatarDataIso(String iso) {
        try {
            String[] p = iso.split("-");
            return p.length == 3 ? p[2] + "/" + p[1] + "/" + p[0] : iso;
        } catch (Exception e) { return iso; }
    }

    private void solicitarPermissaoNotificacoes() {
        if (!adminNotificacoes()) return;
        if (Build.VERSION.SDK_INT >= 33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, 410);
        }
    }

    private void adicionarEstadoNotificacoesNovoTempo(LinearLayout destino) {
        NotificationManager manager = (NotificationManager) getSystemService(Context.NOTIFICATION_SERVICE);
        boolean habilitadas = manager != null && manager.areNotificationsEnabled();
        if (Build.VERSION.SDK_INT >= 33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            habilitadas = false;
        }
        if (Build.VERSION.SDK_INT >= 26 && manager != null) {
            NotificationChannel channel = manager.getNotificationChannel("cobrancas_novo_tempo_v1");
            if (channel != null && channel.getImportance() == NotificationManager.IMPORTANCE_NONE) habilitadas = false;
        }
        TextView estado = texto(NewTempoCollectionReceiver.estadoUltimaVerificacao(this), 12, false);
        estado.setPadding(dp(12), dp(9), dp(12), dp(9));
        estado.setBackground(fundoComBorda(habilitadas ? Color.rgb(237, 247, 239) : Color.rgb(255, 244, 230),
            habilitadas ? Color.rgb(193, 222, 199) : Color.rgb(242, 194, 120), 9));
        LinearLayout.LayoutParams estadoParams = new LinearLayout.LayoutParams(-1, -2);
        estadoParams.setMargins(0, dp(8), 0, dp(4));
        destino.addView(estado, estadoParams);
        if (!habilitadas) {
            Button configurar = botao("Ativar notificações neste celular", Color.rgb(21, 101, 52));
            destino.addView(configurar);
            configurar.setOnClickListener(v -> abrirConfiguracoesNotificacoes());
        }
        Button testar = botao("Testar notificação Novo Tempo", Color.rgb(21, 101, 52));
        LinearLayout.LayoutParams acaoParams = new LinearLayout.LayoutParams(-1, -2);
        acaoParams.setMargins(0, dp(5), 0, dp(3));
        destino.addView(testar, acaoParams);
        testar.setOnClickListener(v -> aviso(NewTempoCollectionReceiver.testarNotificacao(this)));

        if (Build.VERSION.SDK_INT >= 31) {
            AlarmManager alarm = (AlarmManager) getSystemService(Context.ALARM_SERVICE);
            if (alarm != null && !alarm.canScheduleExactAlarms()) {
                Button horarioExato = botao("Permitir horários exatos no Android", Color.rgb(71, 85, 105));
                destino.addView(horarioExato);
                horarioExato.setOnClickListener(v -> abrirConfiguracoesAlarmesExatos());
            }
        }

        Button verificar = botao("Verificar cobranças agora", Color.rgb(37, 99, 235));
        LinearLayout.LayoutParams verificarParams = new LinearLayout.LayoutParams(-1, -2);
        verificarParams.setMargins(0, dp(3), 0, dp(8));
        destino.addView(verificar, verificarParams);
        verificar.setOnClickListener(v -> {
            estado.setText("Consulta iniciada no servidor. Atualizando o resultado...");
            NewTempoCollectionReceiver.verificarAgora(this);
            aviso("Verificação solicitada. O resultado aparecerá abaixo em alguns segundos.");
            estado.postDelayed(() -> estado.setText(NewTempoCollectionReceiver.estadoUltimaVerificacao(this)), 25000);
        });
    }

    private void abrirConfiguracoesNotificacoes() {
        try {
            Intent intent = new Intent(Settings.ACTION_APP_NOTIFICATION_SETTINGS)
                .putExtra(Settings.EXTRA_APP_PACKAGE, getPackageName());
            startActivity(intent);
        } catch (Exception e) {
            Intent intent = new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS,
                Uri.parse("package:" + getPackageName()));
            startActivity(intent);
        }
    }

    private void abrirConfiguracoesAlarmesExatos() {
        if (Build.VERSION.SDK_INT < 31) return;
        try {
            startActivity(new Intent(Settings.ACTION_REQUEST_SCHEDULE_EXACT_ALARM,
                Uri.parse("package:" + getPackageName())));
        } catch (Exception e) {
            aviso("Abra Configurações > Aplicativos > Menina dos Raios > Alarmes e lembretes.");
        }
    }

    private byte[] lerFluxo(java.io.InputStream fluxo) throws Exception {
        if (fluxo == null) return new byte[0];
        try (BufferedInputStream entrada = new BufferedInputStream(fluxo);
             ByteArrayOutputStream saida = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[4096]; int lidos;
            while ((lidos = entrada.read(buffer)) != -1) saida.write(buffer, 0, lidos);
            return saida.toByteArray();
        }
    }

    private String criarMensagem(String nomeCliente) {
        StringBuilder texto = new StringBuilder();
        texto.append("*NOME DO CLIENTE:* ").append(nomeClienteMaiusculo(nomeCliente)).append('\n');
        texto.append("*DATA:* ").append(data.getText()).append("\n\n");
        texto.append("*PEDIDO*\n");
        double total = 0;
        for (ItemPedido i : itens) {
            total += i.total();
            texto.append("• *PRODUTO:* ").append(i.produto)
                .append(" > *").append(rotuloMedida(i.unidade).toUpperCase()).append(":* ").append(formatarNumero(i.peso)).append(' ').append(i.unidade)
                .append(" > *VALOR:* ").append(i.valorInformado ? moeda.format(i.total()) : "—").append('\n');
        }
        texto.append("\n*TOTAL:* ").append(moeda.format(total));
        return texto.toString();
    }

    private void verificarAtualizacao(boolean mostrarResultado) {
        if (mostrarResultado) aviso("Verificando atualizações...");
        new Thread(() -> {
            HttpURLConnection conexao = null;
            try {
                conexao = abrirConexao(UPDATE_URL);
                String json = new String(lerTudo(conexao), "UTF-8");
                JSONObject info = new JSONObject(json);
                int codigo = info.getInt("versionCode");
                if (codigo > obterCodigoVersao()) {
                    String versao = info.optString("versionName", String.valueOf(codigo));
                    String notas = info.optString("releaseNotes", info.optString("notes", "Nova versão disponível."));
                    String apkUrl = info.getString("apkUrl");
                    String sha256 = info.getString("sha256");
                    String pacote = info.optString("packageName", "");
                    long tamanho = info.optLong("sizeBytes", -1L);
                    runOnUiThread(() -> mostrarAtualizacao(versao, notas, apkUrl, sha256, pacote, codigo, tamanho));
                } else if (mostrarResultado) {
                    runOnUiThread(() -> aviso("Você já está usando a versão mais recente (" + obterNomeVersao() + ")."));
                }
            } catch (Exception e) {
                if (mostrarResultado) runOnUiThread(() -> aviso("Não foi possível verificar: " + e.getMessage()));
            } finally {
                if (conexao != null) conexao.disconnect();
            }
        }).start();
    }

    private void mostrarAtualizacao(String versao, String notas, String apkUrl, String sha256,
                                    String pacote, int codigo, long tamanhoEsperado) {
        Dialog dialog = new Dialog(this);
        LinearLayout raiz = coluna();
        raiz.setPadding(dp(22), dp(20), dp(22), dp(18));
        raiz.setBackground(fundoComBorda(Color.WHITE, Color.rgb(221, 231, 224), 22));
        TextView titulo = texto("Atualizações", 23, true);
        titulo.setTextColor(Color.rgb(20, 83, 45));
        raiz.addView(titulo);
        TextView atual = texto("VERSÃO ATUAL  " + obterNomeVersao() + "  ·  NOVA VERSÃO  " + versao,
            12, true);
        atual.setTextColor(COR_TEXTO_SUAVE);
        atual.setPadding(0, dp(8), 0, dp(12));
        raiz.addView(atual);
        LinearLayout card = coluna();
        card.setPadding(dp(15), dp(14), dp(15), dp(14));
        card.setBackground(fundoComBorda(Color.rgb(246, 249, 246), Color.rgb(225, 234, 227), 16));
        TextView status = texto("●  Atualização oficial disponível", 15, true);
        status.setTextColor(Color.rgb(21, 101, 52));
        card.addView(status);
        TextView descricao = texto(notas == null || notas.trim().isEmpty() ? "Correções e melhorias." : notas,
            14, false);
        descricao.setPadding(0, dp(10), 0, 0);
        card.addView(descricao);
        raiz.addView(card);
        ProgressBar progresso = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        progresso.setMax(100);
        progresso.setProgress(0);
        progresso.setVisibility(View.GONE);
        LinearLayout.LayoutParams lpProgress = new LinearLayout.LayoutParams(-1, dp(8));
        lpProgress.setMargins(0, dp(17), 0, dp(6));
        raiz.addView(progresso, lpProgress);
        TextView detalhe = texto("A instalação é validada antes de abrir a confirmação segura do Android.", 12, false);
        raiz.addView(detalhe);
        LinearLayout botoes = new LinearLayout(this);
        botoes.setGravity(Gravity.END | Gravity.CENTER_VERTICAL);
        botoes.setPadding(0, dp(16), 0, 0);
        Button depois = botao("Agora não", Color.rgb(100, 116, 139));
        Button atualizar = botao("Baixar e instalar", Color.rgb(21, 101, 52));
        depois.setTextSize(13);
        atualizar.setTextSize(13);
        LinearLayout.LayoutParams depoisLp = new LinearLayout.LayoutParams(0, dp(50), 1f);
        depoisLp.setMargins(0, 0, dp(5), 0);
        botoes.addView(depois, depoisLp);
        LinearLayout.LayoutParams actionLp = new LinearLayout.LayoutParams(0, dp(50), 1f);
        actionLp.setMargins(dp(5), 0, 0, 0);
        botoes.addView(atualizar, actionLp);
        raiz.addView(botoes);
        dialog.setContentView(raiz);
        dialog.setCancelable(true);
        depois.setOnClickListener(v -> dialog.dismiss());
        atualizar.setOnClickListener(v -> {
            if (Build.VERSION.SDK_INT >= 26 && !getPackageManager().canRequestPackageInstalls()) {
                detalhe.setText("Autorize a instalação pelo Menina dos Raios nas configurações e volte para tocar aqui novamente.");
                Intent permissao = new Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES,
                    Uri.parse("package:" + getPackageName()));
                startActivity(permissao);
                return;
            }
            atualizar.setEnabled(false);
            depois.setEnabled(false);
            progresso.setVisibility(View.VISIBLE);
            detalhe.setText("Preparando download seguro…");
            baixarAtualizacao(apkUrl, sha256, pacote, codigo, tamanhoEsperado, progresso, detalhe, atualizar, dialog);
        });
        dialog.show();
        if (dialog.getWindow() != null) {
            dialog.getWindow().setBackgroundDrawableResource(android.R.color.transparent);
            dialog.getWindow().setLayout(Math.min(getResources().getDisplayMetrics().widthPixels - dp(32), dp(520)),
                android.view.WindowManager.LayoutParams.WRAP_CONTENT);
        }
    }

    private void baixarAtualizacao(String apkUrl, String sha256Esperado, String pacoteEsperado,
                                   int codigoEsperado, long tamanhoEsperado, ProgressBar progresso,
                                   TextView detalhe, Button acao, Dialog dialog) {
        new Thread(() -> {
            HttpURLConnection conexao = null;
            try {
                URL url = new URL(apkUrl);
                if (!"https".equalsIgnoreCase(url.getProtocol())
                    || !"sistema.meninadosraios.com.br".equalsIgnoreCase(url.getHost())
                    || !url.getPath().startsWith("/app-updates/"))
                    throw new SecurityException("O endereço não pertence ao servidor oficial de atualizações.");
                if (!getPackageName().equals(pacoteEsperado) || codigoEsperado <= obterCodigoVersao())
                    throw new SecurityException("Os dados desta versão não correspondem a este aplicativo.");
                if (sha256Esperado == null || !sha256Esperado.matches("(?i)[0-9a-f]{64}"))
                    throw new SecurityException("O checksum informado é inválido.");
                conexao = abrirConexao(apkUrl);
                String hostFinal = conexao.getURL().getHost();
                if (!"sistema.meninadosraios.com.br".equalsIgnoreCase(hostFinal))
                    throw new SecurityException("O download saiu do servidor oficial.");
                long totalBytes = conexao.getContentLength();
                if (tamanhoEsperado > 0 && totalBytes > 0 && tamanhoEsperado != totalBytes)
                    throw new SecurityException("O tamanho publicado não corresponde ao arquivo recebido.");
                File pasta = new File(getCacheDir(), "updates");
                if (!pasta.exists() && !pasta.mkdirs()) throw new Exception("Não foi possível preparar o download.");
                File apk = new File(pasta, "Menina-dos-Raios-Vendas-atualizacao.apk");
                MessageDigest digest = MessageDigest.getInstance("SHA-256");
                final long total = totalBytes;
                final long[] baixados = {0};
                try (BufferedInputStream entrada = new BufferedInputStream(conexao.getInputStream());
                     FileOutputStream saida = new FileOutputStream(apk)) {
                    byte[] buffer = new byte[16384]; int lidos;
                    while ((lidos = entrada.read(buffer)) != -1) {
                        saida.write(buffer, 0, lidos); digest.update(buffer, 0, lidos); baixados[0] += lidos;
                        if (total > 0) {
                            int percentual = (int) Math.min(99, baixados[0] * 100 / total);
                            runOnUiThread(() -> { progresso.setProgress(percentual); detalhe.setText("Baixando atualização… " + percentual + "%"); });
                        }
                    }
                }
                if (tamanhoEsperado > 0 && apk.length() != tamanhoEsperado)
                    throw new SecurityException("O tamanho final do APK não confere com o catálogo.");
                String recebido = hexadecimal(digest.digest());
                if (!recebido.equalsIgnoreCase(sha256Esperado.trim())) {
                    apk.delete(); throw new SecurityException("O arquivo baixado não passou na validação de segurança.");
                }
                validarApkBaixado(apk, pacoteEsperado, codigoEsperado);
                runOnUiThread(() -> {
                    progresso.setProgress(100);
                    detalhe.setText("Download verificado · abrindo a confirmação do Android…");
                    instalarAtualizacao(apk, pacoteEsperado, dialog);
                });
            } catch (Exception e) {
                runOnUiThread(() -> {
                    detalhe.setText("Não foi possível atualizar: " + (e.getMessage() == null ? "falha de validação" : e.getMessage()));
                    progresso.setVisibility(View.GONE);
                    acao.setEnabled(true);
                    aviso("Atualização não instalada. " + (e.getMessage() == null ? "Verifique a conexão." : e.getMessage()));
                });
            } finally {
                if (conexao != null) conexao.disconnect();
            }
        }).start();
    }

    private void validarApkBaixado(File apk, String pacoteEsperado, int codigoEsperado) throws Exception {
        android.content.pm.PackageInfo arquivado;
        if (Build.VERSION.SDK_INT >= 28) {
            arquivado = getPackageManager().getPackageArchiveInfo(apk.getAbsolutePath(), PackageManager.GET_SIGNING_CERTIFICATES);
        } else {
            arquivado = getPackageManager().getPackageArchiveInfo(apk.getAbsolutePath(), PackageManager.GET_SIGNATURES);
        }
        if (arquivado == null || !pacoteEsperado.equals(arquivado.packageName))
            throw new SecurityException("O APK baixado não é o aplicativo esperado.");
        long codigoArquivo = Build.VERSION.SDK_INT >= 28 ? arquivado.getLongVersionCode() : arquivado.versionCode;
        if (codigoArquivo != codigoEsperado) throw new SecurityException("A versão do APK não corresponde ao catálogo.");
        android.content.pm.PackageInfo instalado = getPackageManager().getPackageInfo(getPackageName(),
            Build.VERSION.SDK_INT >= 28 ? PackageManager.GET_SIGNING_CERTIFICATES : PackageManager.GET_SIGNATURES);
        android.content.pm.Signature[] assinaturasAtuais = Build.VERSION.SDK_INT >= 28
            ? instalado.signingInfo.getApkContentsSigners() : instalado.signatures;
        android.content.pm.Signature[] assinaturasArquivo = Build.VERSION.SDK_INT >= 28
            ? arquivado.signingInfo.getApkContentsSigners() : arquivado.signatures;
        if (assinaturasAtuais == null || assinaturasArquivo == null || assinaturasAtuais.length == 0 || assinaturasArquivo.length == 0)
            throw new SecurityException("Não foi possível verificar a assinatura do aplicativo.");
        boolean mesmaAssinatura = false;
        for (android.content.pm.Signature atual : assinaturasAtuais)
            for (android.content.pm.Signature nova : assinaturasArquivo)
                if (atual.equals(nova)) mesmaAssinatura = true;
        if (!mesmaAssinatura) throw new SecurityException("A assinatura digital não corresponde à versão instalada.");
    }

    private HttpURLConnection abrirConexao(String endereco) throws Exception {
        URL url = new URL(endereco);
        if (!"https".equalsIgnoreCase(url.getProtocol())) throw new SecurityException("Endereço de atualização inseguro.");
        HttpURLConnection conexao = (HttpURLConnection) url.openConnection();
        conexao.setConnectTimeout(12000); conexao.setReadTimeout(30000);
        conexao.setRequestProperty("Cache-Control", "no-cache");
        int status = conexao.getResponseCode();
        if (status < 200 || status >= 300) throw new Exception("servidor respondeu " + status);
        return conexao;
    }

    private byte[] lerTudo(HttpURLConnection conexao) throws Exception {
        try (BufferedInputStream entrada = new BufferedInputStream(conexao.getInputStream());
             ByteArrayOutputStream saida = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[4096]; int lidos;
            while ((lidos = entrada.read(buffer)) != -1) saida.write(buffer, 0, lidos);
            return saida.toByteArray();
        }
    }

    private String hexadecimal(byte[] bytes) {
        StringBuilder resultado = new StringBuilder();
        for (byte b : bytes) resultado.append(String.format(Locale.US, "%02x", b & 0xff));
        return resultado.toString();
    }

    private void instalarAtualizacao(File apk, String pacote, Dialog dialog) {
        if (android.os.Build.VERSION.SDK_INT >= 26 && !getPackageManager().canRequestPackageInstalls()) {
            if (dialog != null) dialog.dismiss();
            aviso("Permita a instalação pelo Menina dos Raios e tente novamente.");
            Intent permissao = new Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES,
                Uri.parse("package:" + getPackageName()));
            startActivity(permissao);
            return;
        }
        PackageInstaller installer = getPackageManager().getPackageInstaller();
        int id = -1;
        try {
            PackageInstaller.SessionParams params = new PackageInstaller.SessionParams(PackageInstaller.SessionParams.MODE_FULL_INSTALL);
            params.setAppPackageName(pacote);
            params.setSize(apk.length());
            if (Build.VERSION.SDK_INT >= 31)
                params.setRequireUserAction(PackageInstaller.SessionParams.USER_ACTION_NOT_REQUIRED);
            id = installer.createSession(params);
            try (PackageInstaller.Session session = installer.openSession(id)) {
                try (java.io.InputStream input = new java.io.FileInputStream(apk);
                     java.io.OutputStream output = session.openWrite("base.apk", 0, apk.length())) {
                    byte[] buffer = new byte[65536]; int count;
                    while ((count = input.read(buffer)) >= 0) if (count > 0) output.write(buffer, 0, count);
                    session.fsync(output);
                }
            }
            // Commit from a fresh session after the writer session and all of its file descriptors close.
            try (PackageInstaller.Session session = installer.openSession(id)) {
                Intent callback = new Intent(this, AppInstallStatusReceiver.class);
                callback.putExtra("dialog_message", "A atualização foi enviada ao instalador do Android.");
                callback.putExtra("update_apk_name", apk.getName());
                int flags = PendingIntent.FLAG_UPDATE_CURRENT;
                if (Build.VERSION.SDK_INT >= 31) flags |= PendingIntent.FLAG_MUTABLE;
                PendingIntent result = PendingIntent.getBroadcast(this, id, callback, flags);
                session.commit(result.getIntentSender());
            }
            if (dialog != null) dialog.dismiss();
            aviso("Download validado. Confirme a instalação na tela do Android.");
        } catch (Exception e) {
            if (id >= 0) {
                try { installer.abandonSession(id); } catch (Exception ignored) { }
            }
            if (abrirInstaladorPadrao(apk)) {
                if (dialog != null) dialog.dismiss();
                aviso("O fluxo interno falhou; abrimos a confirmação padrão do Android para instalar a atualização.");
                return;
            }
            aviso("Não foi possível abrir o instalador: " + e.getMessage());
        }
    }

    private boolean abrirInstaladorPadrao(File apk) {
        try {
            Uri uri = new Uri.Builder()
                .scheme("content")
                .authority(getPackageName() + ".files")
                .appendPath("updates")
                .appendPath(apk.getName())
                .build();
            Intent intent = new Intent(Intent.ACTION_INSTALL_PACKAGE);
            intent.setData(uri);
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_ACTIVITY_NEW_TASK);
            startActivity(intent);
            return true;
        } catch (Exception ignored) {
            return false;
        }
    }

    @SuppressWarnings("deprecation")
    private long obterCodigoVersao() {
        try {
            android.content.pm.PackageInfo info = getPackageManager().getPackageInfo(getPackageName(), 0);
            return android.os.Build.VERSION.SDK_INT >= 28 ? info.getLongVersionCode() : info.versionCode;
        } catch (Exception e) { return 0; }
    }

    @SuppressWarnings("deprecation")
    private String obterNomeVersao() {
        try { return getPackageManager().getPackageInfo(getPackageName(), 0).versionName; }
        catch (Exception e) { return "atual"; }
    }

    private boolean atualizacaoPropriaAtiva() {
        return getResources().getBoolean(R.bool.self_update_enabled);
    }

    private String decimal(double n) { return String.format(new Locale("pt", "BR"), "%.2f", n); }
    private String formatarNumero(double n) { return n == Math.rint(n) ? String.valueOf((long)n) : decimal(n); }
    private Double numero(String s) { try { return Double.parseDouble(s.trim().replace(',', '.')); } catch (Exception e) { return null; } }
    private Double obterPrecoSalvo(String produtoNome) {
        if (produtoNome == null || produtoNome.isEmpty()) return null;
        String salvo = getSharedPreferences("precos_produtos", MODE_PRIVATE).getString(produtoNome, null);
        return salvo == null ? null : numero(salvo);
    }
    private void salvarPrecoProduto(String produtoNome, double preco) {
        getSharedPreferences("precos_produtos", MODE_PRIVATE).edit()
            .putString(produtoNome, String.valueOf(preco)).apply();
    }
    private void salvarUnidadeProduto(String produtoNome, String codigo) {
        getSharedPreferences("unidades_produtos", MODE_PRIVATE).edit().putString(produtoNome, codigo).apply();
    }
    private String obterUnidadeProduto(String produtoNome) {
        String normalizado = normalizarNomeProduto(produtoNome);
        switch (normalizado) {
            case "ABACAXI": case "MELANCIA": return "UN";
            case "ALFACE": return "MC";
            case "MACA": return "CX";
            case "CHEIRO VERDE": case "COUVE": case "MANJERICAO": return "MC";
            case "LARANJA": return "SC";
            case "ABOBRINHA": case "ALHO": case "ACAFRAO": case "BANANA PACOVAN":
            case "BANANA PRATA": case "BATATA DOCE": case "BATATA INGLESA": case "BETERRABA":
            case "CANELA EM PO": case "CEBOLA": case "CENOURA": case "CHIMICHURRI":
            case "GERGELIM": case "MACAXEIRA": case "MANGA": case "MELAO": case "PEPINO":
            case "PIMENTA": case "PIMENTA DE CHEIRO": case "PIMENTA DO REINO": case "PIMENTAO":
            case "REPOLHO ROXO": case "REPOLHO VERDE": case "TOMATE": case "UVA PASSA":
            case "LIMAO": case "ERVAS FINAS": case "COLORAU": case "MAMAO": case "ABOBORA":
                return "KG";
            default:
                String salva = getSharedPreferences("unidades_produtos", MODE_PRIVATE).getString(produtoNome, null);
                return salva == null ? "KG" : salva;
        }
    }
    private String normalizarNomeProduto(String nome) {
        if (nome == null) return "";
        String maiusculo = nome.trim().toUpperCase(new Locale("pt", "BR"));
        return Normalizer.normalize(maiusculo, Normalizer.Form.NFD).replaceAll("\\p{M}+", "");
    }
    private void selecionarUnidadeDoProduto(String produtoNome) {
        if (unidade == null) return;
        String codigo = obterUnidadeProduto(produtoNome);
        for (int i = 0; i < unidade.getCount(); i++) {
            if (codigo.equals(unidade.getItemAtPosition(i).toString())) { unidade.setSelection(i); break; }
        }
    }
    private void atualizarDicaValor() {
        if (valor == null || produto == null || produto.getSelectedItem() == null) return;
        Double atual = obterPrecoSalvo(produto.getSelectedItem().toString());
        valor.setHint(normalizarTextoExibicao(atual == null
            ? "Valor unitário (informe na primeira vez)"
            : "Valor atual: " + moeda.format(atual) + " — deixe vazio para manter"));
    }
    private void ordenarProdutos() {
        Collator comparador = Collator.getInstance(new Locale("pt", "BR"));
        comparador.setStrength(Collator.PRIMARY);
        Collections.sort(produtos, comparador);
    }
    private String rotuloMedida(String unidade) {
        if ("UN".equals(unidade)) return "Unidade";
        if ("CX".equals(unidade)) return "Caixa";
        if ("MC".equals(unidade)) return "Maço";
        if ("SC".equals(unidade)) return "Saco";
        return "Peso";
    }
    private boolean appInstalado(String p) { try { getPackageManager().getPackageInfo(p, 0); return true; } catch (Exception e) { return false; } }
    private void aviso(String s) { Toast.makeText(this, normalizarTextoExibicao(s), Toast.LENGTH_LONG).show(); }

    private void preencherDataAtual() { data.setText(new SimpleDateFormat("dd/MM/yyyy", Locale.getDefault()).format(Calendar.getInstance().getTime())); }
    private void escolherData() {
        Calendar c = Calendar.getInstance();
        new DatePickerDialog(this, (v, a, m, d) -> data.setText(String.format(Locale.getDefault(), "%02d/%02d/%04d", d, m + 1, a)), c.get(Calendar.YEAR), c.get(Calendar.MONTH), c.get(Calendar.DAY_OF_MONTH)).show();
    }
    private LinearLayout coluna() { LinearLayout l = new LinearLayout(this); l.setOrientation(LinearLayout.VERTICAL); return l; }
    private EditText campo(String dica, int tipo) { EditText e = new EditText(this); e.setHint(normalizarTextoExibicao(dica)); e.setInputType(tipo); e.setSingleLine(true); e.setPadding(dp(10), dp(6), dp(10), dp(6)); e.setMinHeight(dp(44)); e.setLayoutParams(new LinearLayout.LayoutParams(-1, dp(48))); e.setTextColor(COR_TEXTO_CLARO); e.setHintTextColor(COR_TEXTO_SUAVE); e.setBackground(fundoComBorda(Color.WHITE, Color.rgb(216, 227, 220), 10)); return e; }
    private TextView texto(String s, int tamanho, boolean negrito) { TextView t = new TextView(this); t.setText(normalizarTextoExibicao(s)); t.setTextSize(tamanho); t.setTextColor(negrito ? COR_TEXTO_CLARO : COR_TEXTO_SUAVE); t.setPadding(0, dp(4), 0, dp(4)); if (negrito) t.setTypeface(null, 1); return t; }
    private Button botao(String s, int cor) { Button b = new Button(this); b.setText(normalizarTextoExibicao(s)); b.setAllCaps(false); b.setGravity(Gravity.CENTER); b.setTextSize(14); b.setTypeface(null, 1); b.setTextColor(Color.WHITE); b.setBackground(fundoArredondado(cor, 9)); b.setMinHeight(0); b.setMinimumHeight(0); b.setMinWidth(0); b.setMinimumWidth(0); b.setPadding(dp(10), 0, dp(10), 0); b.setElevation(dp(3)); LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(-1, dp(48)); p.setMargins(0, dp(5), 0, dp(5)); b.setLayoutParams(p); aplicarFeedbackToque(b); return b; }
    private ArrayAdapter<String> adaptadorSpinner(String[] itens) { return adaptadorSpinner(new ArrayList<>(Arrays.asList(itens))); }
    private ArrayAdapter<String> adaptadorSpinner(List<String> itens) {
        return new ArrayAdapter<String>(this, android.R.layout.simple_spinner_dropdown_item, itens) {
            @Override public View getView(int position, View convertView, android.view.ViewGroup parent) {
                TextView v = (TextView) super.getView(position, convertView, parent);
                v.setTextColor(temaEscuroAtivo ? COR_TEXTO_CLARO : Color.rgb(31, 41, 55));
                v.setTextSize(14);
                v.setPadding(dp(10), dp(8), dp(10), dp(8));
                return v;
            }
            @Override public View getDropDownView(int position, View convertView, android.view.ViewGroup parent) {
                TextView v = (TextView) super.getDropDownView(position, convertView, parent);
                v.setTextColor(Color.rgb(31, 41, 55));
                v.setTextSize(15);
                v.setPadding(dp(12), dp(10), dp(12), dp(10));
                return v;
            }
        };
    }
    private GradientDrawable fundoArredondado(int cor, int raio) { GradientDrawable fundo = new GradientDrawable(); fundo.setColor(cor); fundo.setCornerRadius(dp(raio)); return fundo; }
    private GradientDrawable fundoComBorda(int cor, int borda, int raio) { GradientDrawable fundo = fundoArredondado(cor, raio); fundo.setStroke(dp(2), borda); return fundo; }
    private GradientDrawable fundoCardEscuro(int cor) { GradientDrawable fundo = new GradientDrawable(); fundo.setColor(COR_CARD_ESCURO); fundo.setCornerRadius(dp(14)); fundo.setStroke(dp(1), cor); return fundo; }
    private GradientDrawable fundoCardModulo(int cor) { GradientDrawable fundo = new GradientDrawable(GradientDrawable.Orientation.TL_BR, new int[]{COR_CARD_ESCURO_2, COR_CARD_ESCURO}); fundo.setCornerRadius(dp(16)); fundo.setStroke(dp(1), cor); return fundo; }
    private void estilizarSpinner(Spinner s, int corBorda) { if (s == null) return; s.setBackground(fundoComBorda(Color.WHITE, Color.rgb(216, 227, 220), 10)); s.setPadding(dp(8), dp(6), dp(8), dp(6)); }
    private void aplicarFeedbackToque(View v) {
        if (v == null) return;
        v.setOnTouchListener((view, event) -> {
            if (event.getAction() == MotionEvent.ACTION_DOWN) {
                view.animate().scaleX(0.97f).scaleY(0.97f).alpha(0.88f).setDuration(90).start();
            } else if (event.getAction() == MotionEvent.ACTION_UP || event.getAction() == MotionEvent.ACTION_CANCEL) {
                view.animate().scaleX(1f).scaleY(1f).alpha(1f).setDuration(120).start();
            }
            return false;
        });
    }
    private String normalizarTextoExibicao(String s) {
        if (s == null) return "";
        String r = s;
        String[][] mapa = {
            {"Ã¡","á"},{"Ã©","é"},{"Ã­","í"},{"Ã³","ó"},{"Ãº","ú"},
            {"ÃÁ","Á"},{"Ã‰","É"},{"Ã","Í"},{"Ã“","Ó"},{"Ãš","Ú"},
            {"Ã£","ã"},{"Ãµ","õ"},{"Ãª","ê"},{"Ã¢","â"},{"Ã´","ô"},{"Ã§","ç"},
            {"ÃƒÂ¡","á"},{"ÃƒÂ©","é"},{"ÃƒÂ­","í"},{"ÃƒÂ³","ó"},{"ÃƒÂº","ú"},
            {"ÃƒÂ£","ã"},{"ÃƒÂµ","õ"},{"ÃƒÂª","ê"},{"ÃƒÂ¢","â"},{"ÃƒÂ§","ç"},
            {"â€¢","•"},{"â€”","—"},{"â€“","–"},{"â†","←"},
            {"â€œ","“"},{"â€","”"},{"â€˜","‘"},{"â€™","’"},
            {"Âº","º"},{"Âª","ª"},{"Â·","·"},{"Â "," "}
        };
        for (String[] item : mapa) r = r.replace(item[0], item[1]);
        r = r.replace("Macaxeira a VÃ¡cuo", "Macaxeira a Vácuo")
             .replace("Macaxeira a VÃƒÂ¡cuo", "Macaxeira a Vácuo")
             .replace("PrÃ©-Cozida", "Pré-Cozida")
             .replace("PrÃƒÂ©-Cozida", "Pré-Cozida")
             .replace("Pre-Cozida", "Pré-Cozida")
             .replace("VÃ¡cuo", "Vácuo")
             .replace("VÃƒÂ¡cuo", "Vácuo");
        return r;
    }
    private void esconderTeclado() {
        View atual = getCurrentFocus();
        if (atual != null) {
            InputMethodManager teclado = (InputMethodManager) getSystemService(Context.INPUT_METHOD_SERVICE);
            if (teclado != null) teclado.hideSoftInputFromWindow(atual.getWindowToken(), 0);
            atual.clearFocus();
        }
    }
    private void mostrarTeclado(View campo) {
        InputMethodManager teclado = (InputMethodManager) getSystemService(Context.INPUT_METHOD_SERVICE);
        if (teclado != null) teclado.showSoftInput(campo, InputMethodManager.SHOW_IMPLICIT);
    }
    private void manterCampoVisivel(ScrollView scroll, View campo) {
        scroll.postDelayed(() -> {
            int destino = Math.max(0, campo.getTop() - dp(90));
            scroll.smoothScrollTo(0, destino);
        }, 280);
    }
    private int dp(int v) { return (int)(v * getResources().getDisplayMetrics().density + .5f); }

    static class ValeRegistro {
        String clientId = "";
        String remoteId = "";
        String solicitanteNome = "";
        String solicitanteKey = "";
        double amount = 0;
        String requestDate = "";
        String assinaturaBase64 = "";
        String signatureFormat = "png";
        String registeredByUsername = "";
        String registeredByName = "";
        String status = "";
        long createdAt = 0L;
    }

    static class ValeResumo {
        String chave = "";
        String nomeExibicao = "";
        int quantidade = 0;
        double total = 0;
        String primeiraData = "";
        String ultimaData = "";
    }

    static class ValesDatabase extends SQLiteOpenHelper {
        private static final String DB_NAME = "vales_local.db";
        private static final int DB_VERSION = 1;

        ValesDatabase(Context context) {
            super(context.getApplicationContext(), DB_NAME, null, DB_VERSION);
        }

        @Override public void onCreate(SQLiteDatabase db) {
            db.execSQL("CREATE TABLE IF NOT EXISTS vales (" +
                "client_id TEXT PRIMARY KEY," +
                "remote_id TEXT," +
                "solicitante_nome TEXT NOT NULL," +
                "solicitante_key TEXT NOT NULL," +
                "amount REAL NOT NULL," +
                "request_date TEXT NOT NULL," +
                "signature_png_base64 TEXT NOT NULL," +
                "signature_format TEXT," +
                "registered_by_username TEXT," +
                "registered_by_name TEXT," +
                "status TEXT NOT NULL," +
                "created_at INTEGER NOT NULL," +
                "synced_at INTEGER DEFAULT 0" +
                ")");
            db.execSQL("CREATE INDEX IF NOT EXISTS idx_vales_solicitante ON vales(solicitante_key)");
            db.execSQL("CREATE INDEX IF NOT EXISTS idx_vales_data ON vales(request_date)");
            db.execSQL("CREATE INDEX IF NOT EXISTS idx_vales_status ON vales(status)");
        }

        @Override public void onUpgrade(SQLiteDatabase db, int oldVersion, int newVersion) {
            onCreate(db);
        }
    }

    static class SignatureView extends View {
        private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Paint guidePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Path path = new Path();
        private boolean empty = true;
        private float lastX, lastY;

        SignatureView(Context context) {
            super(context);
            paint.setColor(Color.rgb(15, 23, 42));
            paint.setStyle(Paint.Style.STROKE);
            paint.setStrokeWidth(6f);
            paint.setStrokeCap(Paint.Cap.ROUND);
            paint.setStrokeJoin(Paint.Join.ROUND);
            guidePaint.setColor(Color.rgb(148, 163, 184));
            guidePaint.setStyle(Paint.Style.STROKE);
            guidePaint.setStrokeWidth(2f);
            setBackgroundColor(Color.TRANSPARENT);
        }

        @Override protected void onDraw(Canvas canvas) {
            super.onDraw(canvas);
            canvas.drawColor(Color.rgb(248, 250, 252));
            float y = Math.max(1, getHeight() - 34);
            canvas.drawLine(24, y, Math.max(24, getWidth() - 24), y, guidePaint);
            canvas.drawPath(path, paint);
        }

        @Override public boolean onTouchEvent(MotionEvent event) {
            float x = event.getX();
            float y = event.getY();
            switch (event.getAction()) {
                case MotionEvent.ACTION_DOWN:
                    disallowParentIntercept(true);
                    path.moveTo(x, y);
                    lastX = x;
                    lastY = y;
                    empty = false;
                    invalidate();
                    return true;
                case MotionEvent.ACTION_MOVE:
                    disallowParentIntercept(true);
                    path.quadTo(lastX, lastY, (x + lastX) / 2f, (y + lastY) / 2f);
                    lastX = x;
                    lastY = y;
                    invalidate();
                    return true;
                case MotionEvent.ACTION_UP:
                    path.lineTo(x, y);
                    disallowParentIntercept(false);
                    invalidate();
                    return true;
                case MotionEvent.ACTION_CANCEL:
                    disallowParentIntercept(false);
                    invalidate();
                    return true;
                default:
                    return true;
            }
        }

        private void disallowParentIntercept(boolean disallow) {
            ViewParent parent = getParent();
            while (parent != null) {
                parent.requestDisallowInterceptTouchEvent(disallow);
                parent = parent.getParent();
            }
        }

        boolean isEmpty() { return empty; }

        void clear() {
            path.reset();
            empty = true;
            invalidate();
        }

        Bitmap toBitmap() {
            int w = Math.max(1, getWidth());
            int h = Math.max(1, getHeight());
            Bitmap bitmap = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888);
            Canvas canvas = new Canvas(bitmap);
            draw(canvas);
            return bitmap;
        }
    }

    static class ItemInterpretado {
        final String produto, unidade;
        final double medida;
        final boolean novo;
        ItemInterpretado(String p, double m, String u) {
            this(p, m, u, false);
        }
        ItemInterpretado(String p, double m, String u, boolean n) {
            produto = p; medida = m; unidade = u; novo = n;
        }
    }

    static class EntregaGrupo {
        final List<String> ids = new ArrayList<>();
        final StringBuilder itens = new StringBuilder();
        String data = "", hora = "", cliente = "", nf = "", entregador = "", placa = "", entregueEm = "";
        boolean entregue = false;
        int produtos = 0;
        double total = 0;
    }

    static class ItemPedido {
        final String produto, unidade; final double peso, valor;
        final boolean valorInformado, novo;
        ItemPedido(String p, double pe, String u, double v, boolean vi) {
            this(p, pe, u, v, vi, false);
        }
        ItemPedido(String p, double pe, String u, double v, boolean vi, boolean n) {
            produto=p; peso=pe; unidade=u; valor=v; valorInformado=vi; novo=n;
        }
        double total() { return peso * valor; }
    }
}

