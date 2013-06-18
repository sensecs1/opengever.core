jQuery(function($){

  // proposal mapping
  var meeting_columns = $('.column')
  meeting_columns.sortable({
    connectWith: $('.column'),
    cursor : 'move',
    revert : true,
    tolerance : 'pointer',
    stop : function(event, ui){

      var meeting_item = ui.item;
      var item = ui.item.parent('.column');
      var ids = []
      item.children('.proposal').each(function(index, el) {
        ids.push(el.id);
      });
      ids = ids.join(',');
      $.post('./map_proposal_save_view',
             {ids : ids,
              meeting : item.attr('id'),
              item : ui.item.attr('id')},
             function(data, status, xhr){
               if (status == 'success'){
                 if (data != 'OK'){
                   meeting_item.attr('id', data)
                   console.info(meeting_item)
                 }
               }
             });
    }
  });

});
