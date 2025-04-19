import puppeteer from 'puppeteer'
import bodyParser from 'body-parser'
import express from 'express'

async function visit(url) {
	const browser = await puppeteer.launch({
		//executablePath: '/usr/bin/google-chrome-stable'
		headless: true,
		args: [
			'--disable-dev-shm-usage',
			'--no-sandbox',
			'--disable-setuid-sandbox',
			'--disable-gpu',
			'--no-gpu',
			'--disable-default-apps',
			'--disable-translate',
			'--disable-device-discovery-notifications',
			'--disable-software-rasterizer',
		]
	});
	const page = await browser.newPage();

	browser.setCookie({
		'name': 'flag',
		'value': process.env.FLAG || 'fake_flag',
		'domain': 'localhost'

	})

	console.log('Visiting URL: "%s".', url);

	let response = await page.goto(url);

	await page.waitForNetworkIdle();

	console.log(await response.text())

	console.log('Visited URL: "%s".', url);

	await browser.close();
}


const app = express();
const port = 5000;

app.use(bodyParser.urlencoded({ extended: false }));

app.get('/report', async (req, res) => {
	let url = req.query.url;

	await visit(url);

	res.send(`
        <!DOCTYPE html>
        <html>
        <head>
            <title>File Reported</title>
        </head>
        <body>
            <h1>File reported successfully. An admin will check it shortly</h1>
        </body>
        </html>
    `);
});

app.listen(port, () => {
	console.log(`Report bot is running on http://localhost:${port}`);
});
