package com.exemplo.vendaswhatsapp;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.DatePickerDialog;
import android.Manifest;
import android.content.ActivityNotFoundException;
import android.content.ClipboardManager;
import android.content.Intent;
import android.content.Context;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
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
import android.graphics.drawable.GradientDrawable;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
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
import android.widget.ImageView;
import android.widget.LinearLayout;
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
    private TextView vozPergunta, vozEstado, vozClienteData;
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
        abrirFluxoInicial();
    }

    @Override protected void onDestroy() {
        liberarReconhecedorVoz();
        if (falaVoz != null) { falaVoz.stop(); falaVoz.shutdown(); falaVoz = null; }
        super.onDestroy();
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
            if (adminNotificacoes()) {
                solicitarPermissaoNotificacoes();
                CalendarNotificationReceiver.agendar(this);
                NewTempoCollectionReceiver.agendar(this);
            }
            if (atualizacaoPropriaAtiva()) verificarAtualizacao(false);
            servicosPosLoginIniciados = true;
        }
        sincronizarValesPendentesSilencioso();
        mostrarHomeModulos();
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
        raiz.setPadding(dp(18), dp(20), dp(18), dp(26));
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
        raiz.addView(cabecalho);

        TextView chamada = texto("Seu dia, em um só lugar", 23, true);
        chamada.setTextColor(Color.rgb(20, 83, 45));
        chamada.setPadding(0, dp(20), 0, dp(3));
        raiz.addView(chamada);
        TextView apoio = texto("Acesse uma operação ou acompanhe os resultados.", 13, false);
        apoio.setPadding(0, 0, 0, dp(12));
        raiz.addView(apoio);
        EditText busca = campo("Buscar módulo", InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS);
        LinearLayout.LayoutParams buscaParams = new LinearLayout.LayoutParams(-1, dp(48));
        buscaParams.setMargins(0, 0, 0, dp(16));
        raiz.addView(busca, buscaParams);

        List<ModuloHome> modulos = new ArrayList<>();
        modulos.add(new ModuloHome("Entregas", "Lançar pedidos e acompanhar notas", "Operação", "EN", Color.rgb(245, 124, 0), () -> mostrarMenuEntregas()));
        modulos.add(new ModuloHome("Vale", "Solicitação com assinatura", "Operação", "VA", Color.rgb(202, 138, 4), () -> abrirModuloVale()));
        modulos.add(new ModuloHome("Dados dos vales", "Consultar solicitações", "Operação", "DV", Color.rgb(14, 165, 233), () -> abrirModuloDadosVales("")));
        if ("admin".equalsIgnoreCase(authPrefs().getString("role", "").trim())) {
            modulos.add(new ModuloHome("Boletos", "Atrasos e clientes acompanhados", "Operação", "BO", Color.rgb(22, 101, 58), () -> abrirModuloBoletos()));
        }
        modulos.add(new ModuloHome("Projeção", "Estimativa de saída", "Análises", "PR", Color.rgb(59, 130, 246), () -> abrirModuloProjecao("30", "", "", "consolidada")));
        modulos.add(new ModuloHome("Avarias", "Ocorrências por período", "Análises", "AV", Color.rgb(220, 38, 38), () -> abrirModuloAvarias("mes")));
        modulos.add(new ModuloHome("Produtividade", "Resumo da equipe", "Análises", "PD", Color.rgb(22, 163, 74), () -> abrirModuloProdutividade("mes")));
        modulos.add(new ModuloHome("Clientes", "Busca e detalhes", "Análises", "CL", Color.rgb(59, 130, 246), () -> abrirModuloClientes("")));
        modulos.add(new ModuloHome("Consolidado", "Totais do período", "Análises", "CO", Color.rgb(168, 85, 247), () -> abrirModuloConsolidado("mes")));
        modulos.add(new ModuloHome("Produtos", "Consultar preços de venda", "Análises", "PR", Color.rgb(13, 148, 136), () -> abrirModuloProdutos()));
        if (adminNotificacoes()) modulos.add(new ModuloHome("Notificações", "Calendário e alertas", "Mais", "NO", Color.rgb(99, 102, 241), () -> abrirCalendarioNotificacoes()));
        modulos.add(new ModuloHome("Atualizações", "Verificar nova versão", "Mais", "AT", Color.rgb(148, 163, 184), () -> verificarAtualizacao(true)));

        LinearLayout listaModulos = coluna();
        raiz.addView(listaModulos);
        renderizarModulosHome(listaModulos, modulos, "");
        busca.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            @Override public void onTextChanged(CharSequence s, int start, int before, int count) {
                renderizarModulosHome(listaModulos, modulos, s == null ? "" : s.toString());
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
            for (ModuloHome modulo : visiveis) {
                LinearLayout.LayoutParams itemParams = new LinearLayout.LayoutParams(-1, dp(76));
                itemParams.setMargins(0, dp(4), 0, dp(4));
                destino.addView(cartaoModuloHome(modulo), itemParams);
            }
        }
        if (encontrados == 0) {
            TextView vazio = texto("Nenhum módulo encontrado.", 14, false);
            vazio.setGravity(Gravity.CENTER);
            vazio.setPadding(0, dp(20), 0, dp(20));
            destino.addView(vazio);
        }
    }

    private View cartaoModuloHome(ModuloHome modulo) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.HORIZONTAL);
        card.setGravity(Gravity.CENTER_VERTICAL);
        card.setPadding(dp(12), dp(10), dp(12), dp(10));
        card.setBackground(fundoComBorda(COR_CARD_ESCURO, Color.rgb(216, 227, 220), 12));

        TextView sigla = new TextView(this);
        sigla.setText(modulo.sigla);
        sigla.setTextColor(modulo.cor);
        sigla.setTextSize(11);
        sigla.setTypeface(null, 1);
        sigla.setGravity(Gravity.CENTER);
        sigla.setBackground(fundoComBorda(Color.rgb(232, 243, 235), Color.rgb(209, 227, 215), 12));
        card.addView(sigla, new LinearLayout.LayoutParams(dp(42), dp(42)));

        LinearLayout textos = coluna();
        textos.setPadding(dp(12), 0, dp(6), 0);
        TextView titulo = texto(modulo.titulo, 15, true);
        titulo.setSingleLine(true);
        titulo.setEllipsize(android.text.TextUtils.TruncateAt.END);
        TextView descricao = texto(modulo.descricao, 12, false);
        descricao.setSingleLine(true);
        descricao.setEllipsize(android.text.TextUtils.TruncateAt.END);
        textos.addView(titulo);
        textos.addView(descricao);
        card.addView(textos, new LinearLayout.LayoutParams(0, -2, 1));
        TextView seta = texto("›", 24, true);
        seta.setTextColor(COR_TEXTO_SUAVE);
        card.addView(seta);
        card.setOnClickListener(v -> modulo.acao.run());
        card.setFocusable(true);
        aplicarFeedbackToque(card);
        return card;
    }

    private View botaoModulo(String titulo, String descricao, int cor, Runnable acao) {
        LinearLayout card = coluna();
        card.setGravity(Gravity.CENTER_VERTICAL);
        card.setPadding(dp(14), dp(10), dp(14), dp(10));
        card.setBackground(fundoCardModulo(cor));
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-1, dp(96));
        params.setMargins(0, dp(7), 0, dp(7));
        card.setLayoutParams(params);
        TextView t = texto(titulo, 18, true);
        t.setTextColor(COR_TEXTO_CLARO);
        t.setGravity(Gravity.CENTER_HORIZONTAL);
        TextView d = texto(descricao, 13, false);
        d.setTextColor(COR_TEXTO_SUAVE);
        d.setGravity(Gravity.CENTER_HORIZONTAL);
        d.setMaxLines(2);
        card.addView(t);
        card.addView(d);
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
        TextView secao = texto("O que você vai fazer?", 16, true);
        secao.setPadding(0, dp(12), 0, dp(6));
        raiz.addView(secao);
        raiz.addView(botaoModulo("Lançar entrega / pedido", "Adicionar itens e enviar ao ERP", Color.rgb(21, 101, 52), () -> abrirTelaPedido()));
        raiz.addView(botaoModulo("Entrega por voz", "Ditado rápido de cliente e produtos", Color.rgb(21, 101, 52), () -> iniciarEntregaPorVoz()));
        raiz.addView(botaoModulo("Acompanhar entregas", "Ver notas pendentes e concluídas", Color.rgb(21, 101, 52), () -> abrirModuloEntregas(false)));
        setContentView(scroll);
    }

    private void iniciarEntregaPorVoz() {
        if (!SpeechRecognizer.isRecognitionAvailable(this)) {
            new AlertDialog.Builder(this).setTitle("Voz indisponível")
                .setMessage("Este celular não tem um serviço de reconhecimento de voz instalado. Use Lançar entrega / pedido ou instale/ative o reconhecimento de voz do Google.")
                .setPositiveButton("Voltar", (d, w) -> mostrarMenuEntregas()).show();
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

    @Override public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == PEDIDO_AUDIO_VOZ) {
            if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) iniciarEntregaPorVoz();
            else new AlertDialog.Builder(this).setTitle("Microfone não autorizado")
                .setMessage("Ative a permissão de microfone para usar Entrega por voz.")
                .setPositiveButton("OK", (d, w) -> mostrarMenuEntregas()).show();
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
        adicionarCabecalhoModulo(vozRaiz, "Entrega por voz", "Lance o pedido falando com o celular.");
        vozClienteData = texto("Cliente ainda não informado\nData da nota: " + dataVoz, 16, true);
        vozClienteData.setPadding(dp(14), dp(14), dp(14), dp(14));
        vozClienteData.setBackground(fundoComBorda(Color.WHITE, Color.rgb(216, 227, 220), 10));
        vozRaiz.addView(vozClienteData);
        vozPergunta = texto("Preparando conversa...", 21, true);
        vozPergunta.setTextColor(Color.rgb(20, 33, 46));
        vozPergunta.setGravity(Gravity.CENTER);
        vozPergunta.setPadding(dp(8), dp(22), dp(8), dp(12));
        vozRaiz.addView(vozPergunta);
        vozEstado = texto("Toque no microfone para falar", 15, false);
        vozEstado.setTextColor(Color.rgb(100, 116, 139));
        vozEstado.setGravity(Gravity.CENTER);
        vozRaiz.addView(vozEstado);
        vozMicrofone = botao("🎙  FALAR", Color.rgb(21, 101, 52));
        vozMicrofone.setTextSize(24);
        vozMicrofone.setBackground(fundoArredondado(Color.rgb(21, 101, 52), 14));
        vozMicrofone.setContentDescription("Começar a falar o nome do cliente ou os produtos");
        LinearLayout.LayoutParams micParams = new LinearLayout.LayoutParams(-1, dp(112));
        micParams.setMargins(0, dp(16), 0, dp(12));
        vozRaiz.addView(vozMicrofone, micParams);
        vozMicrofone.setOnClickListener(v -> ouvirVoz());
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
        TextView secao = texto("Produtos do pedido", 17, true);
        secao.setPadding(0, dp(22), 0, dp(6));
        vozRaiz.addView(secao);
        vozLista = coluna();
        vozRaiz.addView(vozLista);
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
        if (vozMicrofone != null) { vozMicrofone.setEnabled(true); vozMicrofone.setText("🎙  FALAR"); }
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
        if ("ESTOQUE".equals(nomeClienteMaiusculo(clienteVoz))) {
            StringBuilder resumo = new StringBuilder("A nota será enviada e estes itens serão somados ao estoque da Menina dos Raios:\n\n");
            for (ItemInterpretado item : itensVoz) {
                String produto = item.produto;
                String unidade = item.unidade;
                String normalizado = normalizarNomeProduto(produto).replaceAll("[^A-Z0-9]", "");
                if (normalizado.matches("ALHO(DESCASCADO)?(250(G|GR|GRAMAS))?")) { produto = "Alho 250g"; unidade = "UN"; }
                else if (normalizado.matches("MACAXEIRA(A)?VACUO")) { produto = "Macaxeira a Vácuo"; unidade = "UN"; }
                resumo.append("• ").append(produto).append(" — ").append(formatarNumero(item.medida)).append(" ").append(unidade).append('\n');
            }
            resumo.append("Confirma o envio e a entrada no estoque?");
            new AlertDialog.Builder(this).setTitle("Confirmar entrada no estoque")
                .setMessage(resumo.toString())
                .setNegativeButton("Voltar e corrigir", (dialog, which) -> {
                    perguntarVoz("confirmar_produtos", "Corrija os itens e depois confirme a lista.");
                })
                .setPositiveButton("Confirmar e enviar", (dialog, which) -> prepararNotaVozParaEnvio())
                .show();
            return;
        }
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
        falaPronta = false; vozRaiz = null; vozLista = null; vozPergunta = null; vozEstado = null; vozMicrofone = null; vozClienteData = null; vozSim = null; vozNao = null;
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

        LinearLayout abas = new LinearLayout(this);
        abas.setOrientation(LinearLayout.HORIZONTAL);
        Button pendentes = botaoFiltroBoleto("Pendentes", "pendente");
        Button vencidos = botaoFiltroBoleto("Vencidos", "vencido");
        Button pagos = botaoFiltroBoleto("Pagos", "pago");
        Button alertasNovoTempo = botaoFiltroBoleto("Alertas", "alertas");
        abas.addView(pendentes, new LinearLayout.LayoutParams(0, dp(44), 1));
        abas.addView(vencidos, new LinearLayout.LayoutParams(0, dp(44), 1));
        abas.addView(pagos, new LinearLayout.LayoutParams(0, dp(44), 1));
        abas.addView(alertasNovoTempo, new LinearLayout.LayoutParams(0, dp(44), 1));
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
        destino.addView(texto("Avisos somente para admins: após 24h, às 08h, 12h, 16h e 20h, até a baixa.", 13, false));
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
        String statusLinha = pago ? "PAGO" : iniciou ? "PENDENTE · " + row.optInt("hours_pending", 0) + "h" : "AGUARDANDO 24H";
        TextView chip = texto(statusLinha, 12, true);
        chip.setTextColor(pago ? Color.rgb(21, 101, 52) : iniciou ? Color.rgb(180, 35, 24) : Color.rgb(130, 82, 0));
        card.addView(chip);
        String alerta = iniciou ? "Próximo aviso " + dataHoraAlertaNovoTempo(row.optString("next_alert_at", ""))
            : "Avisos começam " + dataHoraAlertaNovoTempo(row.optString("alert_starts_at", "")) + " · após 24h";
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
        adicionarFiltrosPeriodo(raiz, periodo, p -> abrirModuloAvarias(p));
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
        LinearLayout raiz = coluna();
        raiz.setPadding(dp(24), dp(28), dp(24), dp(32));
        scroll.addView(raiz);

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
        setContentView(scroll);
        usuario.requestFocus();
        usuario.postDelayed(() -> mostrarTeclado(usuario), 250);
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
        new AlertDialog.Builder(this)
            .setTitle("Usar biometria?")
            .setMessage("Deseja usar biometria para abrir o app neste aparelho?")
            .setNegativeButton("Agora nao", (d, w) -> {
                setBiometriaAtiva(false);
                iniciarAppLogado();
            })
            .setPositiveButton("Ativar biometria", (d, w) -> autenticarBiometria("Ativar biometria", () -> {
                setBiometriaAtiva(true);
                iniciarAppLogado();
            }))
            .show();
    }

    private void mostrarTelaBiometria() {
        telaAtual = "auth";
        ScrollView scroll = new ScrollView(this);
        scroll.setBackgroundColor(COR_FUNDO_ESCURO);
        LinearLayout raiz = coluna();
        raiz.setBackgroundColor(COR_FUNDO_ESCURO);
        raiz.setPadding(dp(24), dp(36), dp(24), dp(32));
        scroll.addView(raiz);
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
        Button usar = botao("Usar biometria", Color.rgb(21, 128, 61));
        usar.setOnClickListener(v -> autenticarBiometria("Entrar no app", () -> iniciarAppLogado()));
        raiz.addView(usar);
        Button umaVez = botao("Entrar sem biometria nesta vez", Color.rgb(75, 85, 99));
        umaVez.setOnClickListener(v -> iniciarAppLogado());
        raiz.addView(umaVez);
        Button sair = botao("Sair da conta", Color.rgb(185, 28, 28));
        sair.setOnClickListener(v -> sairDaConta(true));
        raiz.addView(sair);
        setContentView(scroll);
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
            if (!"admin".equalsIgnoreCase(prefs.getString("role", "").trim())) return "";
            return prefs.getString("token", "").trim();
        } catch (Exception e) {
            return "";
        }
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
        sino.setOnClickListener(v -> abrirCalendarioNotificacoes());
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

        Button colarPedido = botao("Importar pedido do WhatsApp", Color.WHITE);
        colarPedido.setTextSize(14);
        colarPedido.setTextColor(Color.rgb(20, 83, 45));
        colarPedido.setBackground(fundoComBorda(Color.WHITE, Color.rgb(21, 101, 52), 11));
        colarPedido.setOnClickListener(v -> abrirColagemWhatsApp());
        raiz.addView(colarPedido);

        adicionarTituloSecao(raiz, "Cliente e data");
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

        adicionarTituloSecao(raiz, "Produtos");
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
        LinearLayout botoesCatalogo = new LinearLayout(this);
        botoesCatalogo.setOrientation(LinearLayout.HORIZONTAL);
        botoesCatalogo.setGravity(Gravity.CENTER_VERTICAL);
        Button novoProduto = botao("+ Novo produto", Color.WHITE);
        novoProduto.setTextColor(Color.rgb(20, 83, 45));
        novoProduto.setBackground(fundoComBorda(Color.WHITE, Color.rgb(216, 227, 220), 10));
        novoProduto.setOnClickListener(v -> cadastrarNovoProduto());
        LinearLayout.LayoutParams novoParams = new LinearLayout.LayoutParams(0, dp(42), 1);
        novoParams.setMargins(0, dp(2), dp(4), dp(2));
        botoesCatalogo.addView(novoProduto, novoParams);
        Button verProdutos = botao("Gerenciar catálogo", Color.WHITE);
        verProdutos.setTextColor(Color.rgb(20, 83, 45));
        verProdutos.setBackground(fundoComBorda(Color.WHITE, Color.rgb(216, 227, 220), 10));
        verProdutos.setOnClickListener(v -> gerenciarProdutos());
        verProdutos.setTextSize(12);
        LinearLayout.LayoutParams verParams = new LinearLayout.LayoutParams(0, dp(42), 1);
        verParams.setMargins(dp(4), dp(2), 0, dp(2));
        botoesCatalogo.addView(verProdutos, verParams);
        raiz.addView(botoesCatalogo);
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

        adicionarTituloSecao(raiz, "Itens do pedido");
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
                produtosAdapter.notifyDataSetChanged();
                produto.setSelection(produtos.indexOf(nome));
                atualizarDicaValor();
            }).show();
    }

    private void salvarProdutos() {
        ordenarProdutos();
        getSharedPreferences("catalogo", MODE_PRIVATE).edit()
            .putStringSet("produtos", new LinkedHashSet<>(produtos)).apply();
        produtosAdapter.notifyDataSetChanged();
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
                salvarProdutos(); atualizarDicaValor(); aviso("Produto excluído.");
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
            if (envioOrigemVoz && "ESTOQUE".equals(nomeClienteMaiusculo(nomeCliente))) {
                normalizarProdutosEstoque(body);
            }
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

    private void normalizarProdutosEstoque(JSONObject body) throws Exception {
        JSONArray produtosJson = body.optJSONArray("items");
        if (produtosJson == null) return;
        for (int i = 0; i < produtosJson.length(); i++) {
            JSONObject item = produtosJson.optJSONObject(i);
            if (item == null) continue;
            String nome = normalizarNomeProduto(item.optString("product", ""))
                .replaceAll("[^A-Z0-9]", "");
            String produtoCanonico;
            if (nome.matches("ALHO(DESCASCADO)?(250(G|GR|GRAMAS))?")) {
                produtoCanonico = "Alho 250g";
            } else if (nome.matches("MACAXEIRA(A)?VACUO")) {
                produtoCanonico = "Macaxeira a Vácuo";
            } else {
                continue;
            }

            double quantidade = item.optDouble("quantity", Double.NaN);
            if (Double.isNaN(quantidade) || Double.isInfinite(quantidade) || quantidade <= 0) {
                quantidade = item.optDouble("weight", Double.NaN);
            }
            if (Double.isNaN(quantidade) || Double.isInfinite(quantidade) || quantidade <= 0) continue;
            item.put("product", produtoCanonico);
            item.put("unit", "UN");
            item.put("quantity", quantidade);
            item.put("weight", quantidade);
        }
    }

    private void enviarNotaSistema(String nomeCliente, JSONObject body, List<ItemPedido> itensEnvio, String mergeIntoNoteId) {
        definirStatusEnvio("Enviando nota ao servidor...", Color.rgb(37, 99, 235));
        enviarSistemaButton.setEnabled(false);
        enviarSistemaButton.setText("Enviando...");
        try {
            body.put("merge_decided", true);
            body.put("merge_into_note_id", mergeIntoNoteId == null ? "" : mergeIntoNoteId);
            body.put("stock_intake", envioOrigemVoz && "ESTOQUE".equals(nomeClienteMaiusculo(nomeCliente)));
        } catch (Exception e) {
            restaurarBotaoEnvio();
            definirStatusEnvio("Não foi possível iniciar o envio. A nota continua em edição.", Color.rgb(185, 28, 28));
            aviso("Não foi possível preparar a decisão de unificação: " + e.getMessage()); return;
        }
        new Thread(() -> {
            try {
                JSONObject resposta = postarNota(body);
                JSONObject entradaEstoque = resposta.optJSONObject("stock_intake");
                if (body.optBoolean("stock_intake") && entradaEstoque == null)
                    throw new Exception("servidor ainda não confirmou a entrada automática no estoque");
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
                        String confirmacao = "Nota enviada. ";
                        if (body.optBoolean("stock_intake")) {
                            confirmacao += entradaEstoque.optBoolean("duplicate")
                                ? "O estoque já havia sido atualizado para esta nota."
                                : entradaEstoque.optInt("items_added") + " item(ns) somado(s) ao estoque da Menina dos Raios.";
                        } else {
                            confirmacao += "Pode iniciar o próximo pedido.";
                        }
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
            .setPositiveButton("Fechar", null)
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
                    String notas = info.optString("notes", "Nova versão disponível.");
                    String apkUrl = info.getString("apkUrl");
                    String sha256 = info.getString("sha256");
                    runOnUiThread(() -> mostrarAtualizacao(versao, notas, apkUrl, sha256));
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

    private void mostrarAtualizacao(String versao, String notas, String apkUrl, String sha256) {
        new AlertDialog.Builder(this)
            .setTitle("Nova atualização disponível")
            .setMessage("Versão " + versao + "\n\n" + notas + "\n\nDeseja atualizar o aplicativo agora?")
            .setNegativeButton("Agora não", null)
            .setPositiveButton("Atualizar agora", (d, w) -> baixarAtualizacao(apkUrl, sha256))
            .show();
    }

    private void baixarAtualizacao(String apkUrl, String sha256Esperado) {
        aviso("Baixando atualização...");
        new Thread(() -> {
            HttpURLConnection conexao = null;
            try {
                conexao = abrirConexao(apkUrl);
                File pasta = new File(getCacheDir(), "updates");
                if (!pasta.exists() && !pasta.mkdirs()) throw new Exception("Não foi possível preparar o download.");
                File apk = new File(pasta, "Menina-dos-Raios-Vendas-atualizacao.apk");
                MessageDigest digest = MessageDigest.getInstance("SHA-256");
                try (BufferedInputStream entrada = new BufferedInputStream(conexao.getInputStream());
                     FileOutputStream saida = new FileOutputStream(apk)) {
                    byte[] buffer = new byte[16384]; int lidos;
                    while ((lidos = entrada.read(buffer)) != -1) {
                        saida.write(buffer, 0, lidos); digest.update(buffer, 0, lidos);
                    }
                }
                String recebido = hexadecimal(digest.digest());
                if (!recebido.equalsIgnoreCase(sha256Esperado.trim())) {
                    apk.delete(); throw new SecurityException("O arquivo baixado não passou na validação de segurança.");
                }
                runOnUiThread(() -> instalarAtualizacao(apk));
            } catch (Exception e) {
                runOnUiThread(() -> aviso("Falha ao baixar atualização: " + e.getMessage()));
            } finally {
                if (conexao != null) conexao.disconnect();
            }
        }).start();
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

    private void instalarAtualizacao(File apk) {
        if (android.os.Build.VERSION.SDK_INT >= 26 && !getPackageManager().canRequestPackageInstalls()) {
            aviso("Autorize este aplicativo a instalar atualizações e depois toque novamente em Verificar atualizações.");
            Intent permissao = new Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES,
                Uri.parse("package:" + getPackageName()));
            startActivity(permissao); return;
        }
        Uri uri = Uri.parse("content://" + getPackageName() + ".files/updates/" + apk.getName());
        Intent instalar = new Intent(Intent.ACTION_VIEW);
        instalar.setDataAndType(uri, "application/vnd.android.package-archive");
        instalar.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_ACTIVITY_NEW_TASK);
        startActivity(instalar);
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

