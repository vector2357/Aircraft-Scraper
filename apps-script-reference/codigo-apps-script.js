/*
 * CÓPIA DE REFERÊNCIA - Código Google Apps Script
 * Este código deve ser copiado manualmente para o Google Apps Script
*/

function executeScraping() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  
  // Capturar dados de pesquisa da linha 2
  var searchData = getSearchData(sheet);
  
  // Enviar para servidor Python
  var results = sendToPythonServer(searchData);
  
  // Limpar resultados anteriores (a partir da linha 4)
  clearPreviousResults(sheet);
  
  // Preencher novos resultados
  fillResults(sheet, results);
  
  // Ajustar largura das colunas automaticamente
  autoResizeColumns(sheet);
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
    sheet.getRange(6, 1).setValue('Nenhum resultado encontrado'); // Mudei para linha 5
    return;
  }
  
  // Definir cabeçalhos dos resultados na LINHA 5
  var resultHeaders = ['URL', 'Título', 'Preço', 'Localização', 'Ano', 'Fabricante', 'Modelo', 'Horas Restantes Motor 1', 
                      'Horas Restantes Motor 2', 'Horas Totais', 'Motor 1 Horas', 'Motor 1 Status', 'Motor 2 Horas', 
                      'Motor 2 Status', 'Motor 1 TBO', 'Motor 2 TBO', 'Vendedor', 'Telefone'];
  
  // Cabeçalhos na LINHA 5
  //var headerRange = sheet.getRange(5, 1, 1, resultHeaders.length);
  //headerRange.setValues([resultHeaders]);
  //headerRange.setFontWeight('bold');
  
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
      result.motor_1_horas ? (result.motor_1_horas.horas || '') : '', // Corrigido operador ?.
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
    var dataRange = sheet.getRange(6, 1, rowData.length, resultHeaders.length); // Mudei para linha 6
    dataRange.setValues(rowData);
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