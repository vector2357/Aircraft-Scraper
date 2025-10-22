/*
 * CÓPIA DE REFERÊNCIA - Código Google Apps Script
 * Este código deve ser copiado manualmente para o Google Apps Script
*/

function executeScraping() {
  var spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = spreadsheet.getActiveSheet();
  
  // Capturar dados de pesquisa da linha 2
  var searchData = getSearchData(sheet);
  
  // Enviar para servidor Python
  var results = sendToPythonServer(searchData);
  
  // Limpar resultados anteriores (a partir da linha 6)
  clearPreviousResults(sheet);
  
  // Preencher novos resultados
  fillResults(sheet, results);
  
  // Ajustar largura das colunas automaticamente
  autoResizeColumns(sheet);
  
  // Salvar histórico na sub-planilha
  saveToHistory(spreadsheet, searchData, results);
}

function getSearchData(sheet) {
  var dataRange = sheet.getRange(1, 1, 2, 10);
  var data = dataRange.getValues();
  
  var headers = data[0];
  var searchRow = data[1];
  
  var searchData = {
    'manufacturer': null,
    'model': null,
    'country': null,
    'year': {
        "min": null,
        "max": null
    },
    'price': {
        "min": null,
        "max": null
    },
    'engine_left_time_min': "0",
    'engine_left_time_max': "1000000000"
  };
  
  for (var i = 0; i < headers.length; i++) {
    var header = headers[i].toLowerCase().trim();
    var value = searchRow[i];
    if (value) {
      value = value.toString();
    }
    
    switch(header) {
      case 'fabricante':
        searchData.manufacturer = value || null;
        break;
      case 'modelo':
        searchData.model = value || null;
        break;
      case 'pais':
        searchData.country = value || null;
        break;
      case 'ano minimo':
        searchData.year.min = value || null;
        break;
      case 'ano maximo':
        searchData.year.max = value || null;
        break;
      case 'preco minimo':
        searchData.price.min = value || null;
        break;
      case 'preco maximo':
        searchData.price.max = value || null;
        break;
      case 'horas rest. motor minimo':
        searchData.engine_left_time_min = value || "0";
        break;
      case 'horas rest. motor maximo':
        searchData.engine_left_time_max = value || "1000000000";
        break;
    }
  }
  
  return searchData;
}

function parseValue(value) {
  if (!value || value === 'None' || value === 'null') {
    return null;
  }
  // Tentar converter para número se possível
  var num = Number(value);
  return isNaN(num) ? value.trim() : num;
}

function sendToPythonServer(searchData) {
  var serverUrl = 'https://pamela-overmighty-roxann.ngrok-free.dev'
  
  if (!serverUrl) {
    throw new Error('URL do servidor Python não configurada. Defina a propriedade PYTHON_SERVER_URL.');
  }
  
  var options = {
    'method': 'POST',
    'headers': {
      'Content-Type': 'application/json',
    },
    'payload': JSON.stringify(searchData),
    'muteHttpExceptions': true
  };
  
  var response = UrlFetchApp.fetch(serverUrl + '/scrape', options);
  var responseCode = response.getResponseCode();
  
  if (responseCode !== 200) {
    throw new Error('Erro no servidor: ' + responseCode + ' - ' + response.getContentText());
  }
  
  var results = JSON.parse(response.getContentText());
  return results;
}

function clearPreviousResults(sheet) {
  var lastRow = sheet.getLastRow();
  if (lastRow > 5) { // (limpar a partir da linha 6)
    sheet.getRange(6, 1, lastRow - 4, sheet.getLastColumn()).clearContent();
  }
}

function fillResults(sheet, results) {
  debugResults(results);
  if (!results || results.length === 0) {
    sheet.getRange(6, 1).setValue('Nenhum resultado encontrado');
    return;
  }
  
  // Definir cabeçalhos dos resultados na LINHA 5
  var resultHeaders = ['URL', 'Título', 'Preço', 'Localização', 'Ano', 'Fabricante', 'Modelo', 'Horas Restantes Motor 1', 
                      'Horas Restantes Motor 2', 'Horas Totais', 'Motor 1 Horas', 'Motor 1 Status', 'Motor 2 Horas', 
                      'Motor 2 Status', 'Motor 1 TBO', 'Motor 2 TBO', 'Vendedor', 'Telefone'];
  
  // Verificar se já existem cabeçalhos
  var currentHeader = sheet.getRange(5, 1, 1, resultHeaders.length).getValues()[0];
  var hasHeaders = currentHeader.some(function(cell) { return cell !== ''; });
  
  if (!hasHeaders) {
    var headerRange = sheet.getRange(5, 1, 1, resultHeaders.length);
    headerRange.setValues([resultHeaders]);
    headerRange.setFontWeight('bold');
  }
  
  // Preencher dados
  var rowData = [];
  for (var i = 0; i < results.length; i++) {
    var result = results[i];
    var row = [
      result.url || '',
      result.titulo || '',
      result.preco || '',
      result.localizacao || '',
      result.ano || '',
      result.fabricante || '',
      result.modelo || '',
      result.motor_1_left || '',
      result.motor_2_left || '',
      result.horas_totais || '',
      result.motor_1_horas ? (result.motor_1_horas.horas || '') : '',
      result.motor_1_horas ? (result.motor_1_horas.status || '') : '',
      result.motor_2_horas ? (result.motor_2_horas.horas || '') : '',
      result.motor_2_horas ? (result.motor_2_horas.status || '') : '',
      result.motor_1_tbo || '',
      result.motor_2_tbo || '',
      result.vendedor || '',
      result.telefone || ''
    ];
    rowData.push(row);
  }
  
  if (rowData.length > 0) {
    // Dados começam na LINHA 6 (5 + 1)
    var dataRange = sheet.getRange(6, 1, rowData.length, resultHeaders.length);
    dataRange.setValues(rowData);

    formatMainSheetData(sheet, rowData.length, resultHeaders.length);
  }
}

function debugResults(results) {
  Logger.log('=== 🔍 DEBUG RESULTS JSON ===');
  
  if (!results) {
    Logger.log('❌ Results é null ou undefined');
    return;
  }
  
  Logger.log('📊 Tipo de results: ' + typeof results);
  Logger.log('📊 Número de resultados: ' + results.length);
  
  // Verificar estrutura do primeiro resultado
  if (results.length > 0) {
    Logger.log('\n🎯 PRIMEIRO RESULTADO:');
    Logger.log(JSON.stringify(results[0], null, 2));
    
    // Verificar campos específicos
    var firstResult = results[0];
    Logger.log('\n🔍 CAMPOS ESPECÍFICOS:');
    Logger.log('URL: ' + firstResult.url);
    Logger.log('Título: ' + firstResult.titulo);
    Logger.log('Motor 1 Left: ' + firstResult.motor_1_left);
    Logger.log('Motor 2 Left: ' + firstResult.motor_2_left);
    Logger.log('Motor 1 Horas: ' + JSON.stringify(firstResult.motor_1_horas));
    Logger.log('Motor 2 Horas: ' + JSON.stringify(firstResult.motor_2_horas));
  }
  
  Logger.log('=== ✅ FIM DEBUG ===');
}

function autoResizeColumns(sheet) {
  var lastColumn = sheet.getLastColumn();
  for (var i = 1; i <= lastColumn; i++) {
    sheet.autoResizeColumn(i);
  }
}

// Salvar no histórico
function saveToHistory(spreadsheet, searchData, results) {
  var historySheet = getOrCreateHistorySheet(spreadsheet);
  
  // Preparar dados do histórico
  var timestamp = new Date();
  var searchCriteria = JSON.stringify(searchData);
  
  // Para cada resultado, criar uma entrada no histórico
  for (var i = 0; i < results.length; i++) {
    var result = results[i];
    
    var historyRow = [
      timestamp,                          // Data e hora da pesquisa
      searchCriteria,                     // Critérios de pesquisa usados
      '\'' + (result.url || ''),                   // URL do resultado
      '\'' + (result.titulo || ''),                // Título
      '\'' + (result.preco || ''),                 // Preço
      '\'' + (result.localizacao || ''),           // Localização
      '\'' + (result.ano || ''),                   // Ano
      '\'' + (result.fabricante || ''),            // Fabricante
      '\'' + (result.modelo || ''),               // Modelo
      '\'' + (result.motor_1_left || ''),         // Horas Restantes Motor 1
      '\'' + (result.motor_2_left || ''),         // Horas Restantes Motor 2
      '\'' + (result.horas_totais || ''),         // Horas Totais
      '\'' + (result.motor_1_horas ? (result.motor_1_horas.horas || '') : ''),
      '\'' + (result.motor_1_horas ? (result.motor_1_horas.status || '') : ''),
      '\'' + (result.motor_2_horas ? (result.motor_2_horas.horas || '') : ''),
      '\'' + (result.motor_2_horas ? (result.motor_2_horas.status || '') : ''),
      '\'' + (result.motor_1_tbo || ''),          // Motor 1 TBO
      '\'' + (result.motor_2_tbo || ''),          // Motor 2 TBO
      '\'' + (result.vendedor || ''),             // Vendedor
      '\'' + (result.telefone || '')              // Telefone
    ];
    
    // Adicionar linha ao histórico
    historySheet.appendRow(historyRow);
  }
  
  // Aplicar formatação ao histórico
  formatHistorySheet(historySheet);
  
  Logger.log('✅ Histórico salvo com ' + results.length + ' resultados');
}

// Criar ou obter a planilha de histórico
function getOrCreateHistorySheet(spreadsheet) {
  var historySheetName = "Histórico_Pesquisas";
  var historySheet = spreadsheet.getSheetByName(historySheetName);
  
  if (!historySheet) {
    // Criar nova planilha de histórico
    historySheet = spreadsheet.insertSheet(historySheetName);
    
    // Definir cabeçalhos
    var headers = [
      'Data/Hora Pesquisa',
      'Critérios de Pesquisa (JSON)',
      'URL',
      'Título',
      'Preço',
      'Localização',
      'Ano',
      'Fabricante',
      'Modelo',
      'Horas Restantes Motor 1',
      'Horas Restantes Motor 2',
      'Horas Totais',
      'Motor 1 Horas',
      'Motor 1 Status',
      'Motor 2 Horas',
      'Motor 2 Status',
      'Motor 1 TBO',
      'Motor 2 TBO',
      'Vendedor',
      'Telefone'
    ];
    
    historySheet.getRange(1, 1, 1, headers.length).setValues([headers]);
    historySheet.getRange(1, 1, 1, headers.length).setFontWeight('bold');
    
    // Congelar a linha do cabeçalho
    historySheet.setFrozenRows(1);
    
    // Ajustar largura das colunas
    autoResizeColumns(historySheet);
    
    Logger.log('✅ Planilha de histórico criada: ' + historySheetName);
  }
  
  return historySheet;
}

// Formatar dados da planilha principal
function formatMainSheetData(sheet, numRows, numColumns) {
  if (numRows > 0) {
    var dataRange = sheet.getRange(6, 1, numRows, numColumns);
    
    // Aplicar bordas a todos os dados
    dataRange.setBorder(true, true, true, true, true, true, '#cccccc', SpreadsheetApp.BorderStyle.SOLID);
    
    // Aplicar cores alternadas
    for (var i = 0; i < numRows; i++) {
      var rowRange = sheet.getRange(6 + i, 1, 1, numColumns);
      var color = i % 2 === 0 ? '#ffffff' : '#f8f9fa'; // Branco e cinza muito claro
      rowRange.setBackground(color);
    }
    
    // Formatar coluna de preço (coluna 3)
    var priceRange = sheet.getRange(6, 3, numRows, 1);
    priceRange.setNumberFormat('"R$ "#,##0.00');
    
    // Formatar colunas numéricas
    var numericColumns = [5, 8, 9, 10, 11, 13, 15, 16]; // Ano, Horas Motor 1, Horas Motor 2, etc.
    numericColumns.forEach(function(col) {
      if (col <= numColumns) {
        var range = sheet.getRange(6, col, numRows, 1);
        range.setNumberFormat('#,##0');
      }
    });
    
    // Centralizar algumas colunas
    var centerColumns = [4, 5, 8, 9, 10, 11, 12, 13, 14, 15, 16]; // Localização, Ano, Horas, etc.
    centerColumns.forEach(function(col) {
      if (col <= numColumns) {
        var range = sheet.getRange(6, col, numRows, 1);
        range.setHorizontalAlignment('center');
      }
    });
    
    // Ajustar automaticamente as colunas após formatação
    autoResizeColumns(sheet);
  }
}

// Formatar a planilha de histórico
function formatHistorySheet(sheet) {
  var lastRow = sheet.getLastRow();
  var lastColumn = sheet.getLastColumn();
  
  if (lastRow > 1) {
    // Formatar coluna de data/hora
    sheet.getRange(2, 1, lastRow - 1, 1).setNumberFormat('dd/mm/yyyy hh:mm:ss');
    
    // Formatar coluna de preço (assumindo que é a coluna 5)
    var priceRange = sheet.getRange(2, 5, lastRow - 1, 1);
    priceRange.setNumberFormat('"R$ "#,##0.00');
    
    // Aplicar bordas alternadas para melhor legibilidade
    var dataRange = sheet.getRange(2, 1, lastRow - 1, lastColumn);
    
    // Aplicar cores alternadas
    for (var i = 0; i < lastRow - 1; i++) {
      var color = i % 2 === 0 ? '#ffffff' : '#f9f9f9';
      sheet.getRange(i + 2, 1, 1, lastColumn).setBackground(color);
    }
    
    // Auto-ajustar colunas
    autoResizeColumns(sheet);
    
    // Adicionar bordas
    dataRange.setBorder(true, true, true, true, true, true);
  }
}

// Limpar histórico (opcional)
function clearHistory() {
  var spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  var historySheet = spreadsheet.getSheetByName("Histórico_Pesquisas");
  
  if (historySheet) {
    var lastRow = historySheet.getLastRow();
    if (lastRow > 1) {
      historySheet.getRange(2, 1, lastRow - 1, historySheet.getLastColumn()).clearContent();
      Logger.log('✅ Histórico limpo. ' + (lastRow - 1) + ' linhas removidas.');
    } else {
      Logger.log('ℹ️ Histórico já está vazio.');
    }
  } else {
    Logger.log('❌ Planilha de histórico não encontrada.');
  }
}

// Exportar histórico (opcional)
function exportHistory() {
  var spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  var historySheet = spreadsheet.getSheetByName("Histórico_Pesquisas");
  
  if (!historySheet) {
    Logger.log('❌ Planilha de histórico não encontrada');
    return;
  }
  
  var timestamp = new Date().toISOString().slice(0, 19).replace(/[:]/g, '-');
  var exportSheetName = "Histórico_Export_" + timestamp;
  
  // Duplicar a planilha de histórico
  var exportedSheet = historySheet.copyTo(spreadsheet);
  exportedSheet.setName(exportSheetName);
  
  // Mover para a primeira posição
  spreadsheet.setActiveSheet(exportedSheet);
  spreadsheet.moveActiveSheet(1);
  
  Logger.log('✅ Histórico exportado para: ' + exportSheetName);
  return exportedSheet;
}

// Visualizar histórico (opcional)
function viewHistory() {
  var spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  var historySheet = spreadsheet.getSheetByName("Histórico_Pesquisas");
  
  if (historySheet) {
    spreadsheet.setActiveSheet(historySheet);
    Logger.log('✅ Navegando para a planilha de histórico');
  } else {
    Logger.log('❌ Planilha de histórico não encontrada');
  }
}

// Estatísticas do histórico (opcional)
function getHistoryStats() {
  var spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  var historySheet = spreadsheet.getSheetByName("Histórico_Pesquisas");
  
  if (!historySheet) {
    Logger.log('❌ Planilha de histórico não encontrada');
    return;
  }
  
  var lastRow = historySheet.getLastRow();
  var totalEntries = lastRow - 1; // Excluindo cabeçalho
  
  if (totalEntries > 0) {
    // Obter datas da primeira e última entrada
    var firstDate = historySheet.getRange(2, 1).getValue();
    var lastDate = historySheet.getRange(lastRow, 1).getValue();
    
    Logger.log('=== 📊 ESTATÍSTICAS DO HISTÓRICO ===');
    Logger.log('Total de registros: ' + totalEntries);
    Logger.log('Primeira pesquisa: ' + firstDate);
    Logger.log('Última pesquisa: ' + lastDate);
    Logger.log('Período: ' + Math.ceil((lastDate - firstDate) / (1000 * 60 * 60 * 24)) + ' dias');
    Logger.log('=== ✅ FIM ESTATÍSTICAS ===');
    
    return {
      totalEntries: totalEntries,
      firstDate: firstDate,
      lastDate: lastDate
    };
  } else {
    Logger.log('ℹ️ Histórico vazio - nenhuma estatística disponível');
    return null;
  }
}