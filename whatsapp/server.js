import wppconnect from '@wppconnect-team/wppconnect';
import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';

dotenv.config();

const app = express();
app.use(express.json());
app.use(cors());

let client = null;
let whatsappReady = false;

// ==================================================================================
// CREAR CLIENTE WHATSAPP
// ==================================================================================

wppconnect.create({
    session: "doña_flori",
    folderNameToken: "./tokens",
    createPathFileToken: true,
    autoClose: 60000,
    browserWS: "",
    updatesLog: true,
    puppeteerOptions: {
        headless: false,
        args: [
            "--no-sandbox",
            "--disable-setuid-sandbox"
        ],
        ignoreDefaultArgs: [
            "--disable-extensions"
        ]
    },
    logQR: false,
    catchQR: (base64Qr, asciiQR) => {
        console.log("Escanea este QR con WhatsApp:");
        console.log(asciiQR);
    }
})
.then((connected_client) => {
    client = connected_client;
    console.log(typeof client.getConnectionState);
    console.log('✓ WhatsApp conectado correctamente');
    
    client.onStateChange((state) => {
        console.log("Estado WhatsApp:", state);

        whatsappReady = (
            state === "CONNECTED" ||
            state === "MAIN"
        );
    });

    client.onStreamChange((state) => {
        console.log("Stream:", state);

        if (state === "DISCONNECTED") {
            console.log("⛔ Pausando envíos...");
        }

        if (state === "CONNECTED") {
            console.log("✅ WhatsApp volvió a conectarse.");

            setTimeout(() => {
                console.log("Listo para enviar.");
            }, 10000);
        }
    });
})
.catch((err) => {
    console.error('✗ Error conectando WhatsApp:', err);
    process.exit(1);
});

// ==================================================================================
// RUTAS API
// ==================================================================================

// Health check
app.get('/health', (req, res) => {
    res.json({
        ok: true,
        estado: client ? 'conectado' : 'desconectado'
    });
});

// Enviar mensaje de texto con reintentos
app.post('/api/pedidos/send-message', async (req, res) => {

    try {

        const { phone, message } = req.body;

        if (!phone || !message) {
            return res.status(400).json({
                ok: false,
                error: "Faltan parámetros"
            });
        }

        if (!client) {
            return res.status(503).json({
                ok: false,
                error: "WhatsApp no conectado"
            });
        }

        const jid = `${phone}@c.us`;

        const state = await client.getConnectionState();

        if (
            state !== "CONNECTED" &&
            state !== "MAIN"
        ) {
            return res.status(503).json({
                ok: false,
                error: `Estado WhatsApp: ${state}`
            });
        }

        const status = await client.checkNumberStatus(jid);

        if (!status?.numberExists) {
            return res.status(404).json({
                ok: false,
                error: "El número no tiene WhatsApp"
            });
        }

        await client.sendText(jid, message);

        console.log(`✓ Mensaje enviado a ${phone}`);

        return res.json({
            ok: true,
            phone
        });

    } catch (error) {

        console.error(error.message);

        if (
            error.message.includes("reading 'get'") ||
            error.message.includes("getMessageById")
        ) {

            console.log("⚠️ Error conocido de WPPConnect. El mensaje probablemente fue enviado.");

            return res.json({
                ok: true,
                warning: true,
                message: "Mensaje enviado (bug conocido de WPPConnect)"
            });

        }

        return res.status(500).json({
            ok: false,
            error: error.message
        });
    }

});


// Enviar imagen con texto
app.post('/api/pedidos/send-image', async (req, res) => {
    try {
        const { phone, imagePath, caption } = req.body;

        if (!phone || !imagePath) {
            return res.status(400).json({
                ok: false,
                error: 'Faltan parametros: phone e imagePath requeridos'
            });
        }

        if (!client) {
            return res.status(503).json({
                ok: false,
                error: 'WhatsApp no está conectado'
            });
        }

        const jid = `${phone}@c.us`;

        // Usar sendImage directamente
        await client.sendImage(
            jid,
            imagePath,
            'imagen.jpg',
            caption || ''
        );

        console.log(`✓ Imagen enviada a ${phone}`);
        res.json({
            ok: true,
            message: 'Imagen enviada correctamente'
        });

    } catch (error) {
        console.error('✗ Error enviando imagen:', error);
        res.status(500).json({
            ok: false,
            error: error.message
        });
    }
});

// Obtener estado
app.get('/api/status', (req, res) => {
    res.json({
        ok: true,
        conectado: client ? true : false,
        estado: client ? 'listo' : 'desconectado'
    });
});

// ==================================================================================
// INICIAR SERVIDOR
// ==================================================================================

const PORT = process.env.PORT || 21465;

app.listen(PORT, () => {
    console.log(`\n✓ Servidor WhatsApp en puerto ${PORT}`);
    console.log(`✓ Endpoint: POST http://localhost:${PORT}/api/pedidos/send-message`);
    console.log('\n');
});

// Graceful shutdown
process.on('SIGTERM', () => {
    console.log('\nCerrando servidor...');
    process.exit(0);
});