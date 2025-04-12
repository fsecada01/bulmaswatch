// build-themes.js
import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';

const themesDir = 'new_themes';
const outputDir = 'dist/css';
const utilitiesDirName = 'utilities';
const entryFileName = 'bulmaswatch.scss';
// Use 'npx sass' to ensure the locally installed Dart Sass is used
const sassCommand = 'npx sass';
// Use '--no-source-map' for Dart Sass
const sourceMapFlag = '--no-source-map';
// Use '--style=compressed' or '--style=expanded'
const styleFlag = '--style=compressed';

console.log(`Starting CSS build process from '${themesDir}'...`);

// --- 1. Ensure output directory exists ---
try {
    if (!fs.existsSync('dist')) {
        fs.mkdirSync('dist');
        console.log(`Created directory: dist`);
    }
    if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir);
        console.log(`Created directory: ${outputDir}`);
    } else {
        console.log(`Output directory '${outputDir}' already exists.`);
    }
} catch (err) {
    console.error(`Error creating output directory '${outputDir}':`, err);
    process.exit(1);
}

// --- 2. Find theme directories ---
let themeDirs = [];
try {
    themeDirs = fs.readdirSync(themesDir, { withFileTypes: true })
        .filter(dirent => dirent.isDirectory() && dirent.name !== utilitiesDirName)
        .map(dirent => dirent.name);
    console.log(`Found ${themeDirs.length} theme directories.`);
} catch (err) {
    console.error(`Error reading themes directory '${themesDir}':`, err);
    process.exit(1);
}

if (themeDirs.length === 0) {
    console.warn("No theme directories found to process.");
    process.exit(0);
}

// --- 3. Compile each theme ---
let successCount = 0;
let errorCount = 0;

themeDirs.forEach(themeName => {
    const themePath = path.join(themesDir, themeName);
    const inputFile = path.join(themePath, entryFileName);
    const outputFileName = `${themeName}.css`;
    const outputFile = path.join(outputDir, outputFileName);
    // Note: If using --no-source-map, this map file won't actually be created by Sass
    const outputMapFile = `${outputFile}.map`;

    console.log(`\n--- Processing theme: ${themeName} ---`);

    if (!fs.existsSync(inputFile)) {
        console.warn(`Skipping '${themeName}': Entry file '${inputFile}' not found.`);
        errorCount++;
        return;
    }

    // Construct the Dart Sass command
    // Added load paths for node_modules (for bulma) and utilities
    const command = `${sassCommand} "${inputFile}" "${outputFile}" ${sourceMapFlag} ${styleFlag} --load-path=node_modules --load-path=${path.join(themesDir, utilitiesDirName)}`;

    console.log(`Compiling: ${inputFile} -> ${outputFile}`);
    console.log(`Executing: ${command}`);

    try {
        execSync(command, { stdio: 'inherit' });
        console.log(`Successfully compiled ${outputFileName}`);
        successCount++;
    } catch (error) {
        // Error message is often less helpful from execSync, Sass output above is key
        console.error(`Error compiling theme '${themeName}'. See Sass output above for details.`);
        errorCount++;
        // Attempt cleanup
        try {
            if (fs.existsSync(outputFile)) fs.unlinkSync(outputFile);
            // Only try to delete map if source maps weren't disabled
            if (sourceMapFlag !== '--no-source-map' && fs.existsSync(outputMapFile)) {
                fs.unlinkSync(outputMapFile);
            }
        } catch (cleanupError) {
            console.error(`Error cleaning up output for '${themeName}':`, cleanupError);
        }
    }
});

// --- 4. Final Summary ---
console.log('\n--- Build Summary ---');
console.log(`Successfully compiled: ${successCount} themes.`);
console.log(`Failed to compile:   ${errorCount} themes.`);
console.log('---------------------');

if (errorCount > 0) {
    console.error("Build process finished with errors.");
    process.exit(1);
} else {
    console.log("Build process finished successfully.");
    process.exit(0);
}