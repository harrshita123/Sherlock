import { put } from '@vercel/blob';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const fixturesDir = path.join(__dirname, '..', 'fixtures');

async function uploadFixtures() {
  const files = fs.readdirSync(fixturesDir).filter(f => f.endsWith('.dat.gz'));
  
  console.log(`Found ${files.length} fixture files to upload...`);
  
  const uploadedFiles = {};
  
  for (const file of files) {
    const filePath = path.join(fixturesDir, file);
    const fileBuffer = fs.readFileSync(filePath);
    
    console.log(`Uploading ${file} (${(fileBuffer.length / 1024 / 1024).toFixed(2)} MB)...`);
    
    const blob = await put(`fixtures/${file}`, fileBuffer, {
      access: 'public',
      contentType: 'application/gzip',
    });
    
    console.log(`  Uploaded to: ${blob.url}`);
    uploadedFiles[file] = blob.url;
  }
  
  // Also upload the xor.dat file
  const xorPath = path.join(__dirname, '..', 'public', 'fixtures', 'xor.dat');
  if (fs.existsSync(xorPath)) {
    const xorBuffer = fs.readFileSync(xorPath);
    console.log(`Uploading xor.dat...`);
    const blob = await put('fixtures/xor.dat', xorBuffer, {
      access: 'public',
      contentType: 'application/octet-stream',
    });
    console.log(`  Uploaded to: ${blob.url}`);
    uploadedFiles['xor.dat'] = blob.url;
  }
  
  // Save the URLs to a JSON file
  const outputPath = path.join(__dirname, '..', 'public', 'fixtures-urls.json');
  fs.writeFileSync(outputPath, JSON.stringify(uploadedFiles, null, 2));
  console.log(`\nSaved URLs to ${outputPath}`);
  
  return uploadedFiles;
}

uploadFixtures().catch(console.error);
