/* main.js for accounting-related code */

function accountingResetSubcategoryDropdown(catListId, subcatListId, choiceTree, prevFullSubcatId) {
  /*
    this empties and repopulates the ledger-subcategory list (if needed leaving it
    essentially empty) depending on the chosen ledger-category.
    Inputs are the ids of the cat/subcat dropdowns and a map
      category_id -> list of subcat ids.
    Remember the ids in the second dropdown are "CAT_ID.SUBCAT_ID".
  */
  var subcatList = $(`#${subcatListId}`);
  // emptying
  subcatList.empty();
  // filling (incl. empty case)
  var catList = $(`#${catListId}`);
  var chosenCat = catList.val();
  subcats = (choiceTree[chosenCat] || []);
  subcatList.append(
    $('<option></option>').val('').html('Choose subcategory...')
  );
  var fullSubIds = [];
  for(var i = 0; i < subcats.length; i++){
    var subcat = subcats[i];
    var fullSubcatId = `${chosenCat}.${subcat}`;
    subcatList.append(
      $('<option></option>').val(fullSubcatId).html(subcat)
    );
    fullSubIds.push(fullSubcatId);
  }
  if( fullSubIds.indexOf(prevFullSubcatId) >= 0 ){
    subcatList.val(`${prevFullSubcatId}`); 
  }
}

function accountingRefreshGroupDescriptionText(grpListId, grpHelpId, fullIdToDescriptionMap) {
  var grpList = $(`#${grpListId}`);
  var description = fullIdToDescriptionMap[grpList.val()] || '';
  $(`#${grpHelpId}`)[0].innerHTML = description;
}

function accountingAttachGroupDescriptionText(grpListId, grpHelpId, fullIdToDescriptionMap) {
  var grpList = $(`#${grpListId}`);
  grpList.change( function(e) {
    accountingRefreshGroupDescriptionText(grpListId, grpHelpId, fullIdToDescriptionMap);
  });
}