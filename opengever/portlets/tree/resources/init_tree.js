$(function() {
  var portlet = $('.portlet.portletTreePortlet');
  if(portlet.length === 0) {
    return;
  }

  $(document).bind('tree:rendered', function() {
    resize_treeportlet_height();
    scroll_to_selected_item(portlet.find('.portlet-tabs > .tab'));
  });


  var navigation_json = new LocalStorageJSONCache(
      'navigation', portlet.data('navigation-url'));
  var favorites_store = new RepositoryFavorites(
      portlet.data('favorites-url'),
      portlet.data('favorites-cache-param'));
  if ($('#tree-favorites').length === 0) {
    // Favorites are disabled.
    favorites_store = null;
  }

  /* Complete tree tab */
  portlet.find('#tree-complete').bind('portlet-tab:open', function() {
    if ($(this).data('initialized')) {return;} $(this).data('initialized', 'true');

    var tree_node = $(this).find('>ul');
    navigation_json.load(
        function(tree_data) {
          var expand_store = ExpandStore('expanded_uids', 'uid');
          var navtree = make_tree(tree_data, {
            render_condition: function() {
              return this.depth === 0 || expand_store.is_expanded(this.parent);
            },
            onclick: function(node, event) {
              expand_store.expand(node);
            },
            components: [expand_store, favorites_store]
          });
          tree_node.html('');
          navtree.render(tree_node);
          navtree.selectCurrent(find_parent_node_for_url(
              navtree, portlet.data('context-url')));
        });
  });

  /* Favorites tree tab */
  var favorites_tree;
  function render_favorites_tree() {
    var tree_node = portlet.find('#tree-favorites').find('>ul');
    navigation_json.load(function(tree_data) {
      favorites_store.load(function(favorites) {
        var fav_expand_store = ExpandStore('expanded_fav_uids', 'uid');
        var favorite_nodes = make_tree(tree_data).clone_by_uids(favorites);
        sort_by_text(favorite_nodes);
        favorites_tree = make_tree(favorite_nodes, {
          render_condition: function() {
            return this.depth === 0 || fav_expand_store.is_expanded(this.parent);
          },
          onclick: function(node, event) {
            fav_expand_store.expand(node);
          },
          components: [fav_expand_store]
        });
        tree_node.html('');
        favorites_tree.render(tree_node);
        favorites_tree.selectCurrent(find_parent_node_for_url(
            favorites_tree, portlet.data('context-url')));

        if(favorite_nodes.length === 0) {
          portlet.find('#tree-favorites .no-favorites').show();
          portlet.find('#tree-favorites .helptext').show();
        } else {
          portlet.find('#tree-favorites .no-favorites').hide();
          portlet.find('#tree-favorites .helptext').hide();
        }

      });
    });
  }

  portlet.find('#tree-favorites').bind('portlet-tab:open', render_favorites_tree);

  portlet.find('#tree-favorites a.toggle-helptext').click(function(event) {
    event.preventDefault();
    portlet.find('#tree-favorites .helptext').toggle();
  });

  $(favorites_store).bind('favorites:changed', function() {
    if(portlet.find('#tree-favorites').is(':visible')) {
      render_favorites_tree();
    }
  });


  /* Tabs configuration */
  var tabs_count = portlet.find('.portlet-header-tabs li').length;
  var initial_tab_index = 0;
  var current_tab_class = 'active';
  if(tabs_count > 1) {
    initial_tab_index = parseInt($.cookie('tree-portlet-tab-index'), 10) || 0;
  }

  if(tabs_count == 1) {
    /* Change the current-tab-class so that we dont have the default
       styling, which does not look nice with only one tab. */
    current_tab_class = 'the-only-one';
  }

  portlet.find('.portlet-header-tabs').tabs(
      '.portlet-tabs > div', {
        current: current_tab_class,
        tabs: 'li > a',
        initialIndex: initial_tab_index,
        onBeforeClick: function(event, index) {
          $.cookie('tree-portlet-tab-index', index.toString(), {path: '/'});
          $(this.getPanes()[index]).trigger('portlet-tab:open');
        }});


  /* Helpers */

  function find_parent_node_for_url(tree, url) {
    if (!url) {
      return null;
    }

    var node = tree.findBy({'url': url});
    if (node) {
      return node;
    }
    return find_parent_node_for_url(tree, url.slice(0, url.lastIndexOf('/')));
  }

  function resize_treeportlet_height() {
    var tabs = $('dl.portlet.portletTreePortlet .portlet-tabs > .tab');
    var max = $(window).height() - tabs.offset().top - 20;
    tabs.css('max-height', max);
  }
  $(window).resize(resize_treeportlet_height);

  function scroll_to_selected_item(tree) {
    var position = tree.find('a.current').position();
    if (position) {
      $('.portletTreePortlet dd.portletItem').scrollTop(position.top - 60);
    }
  }

  function sort_by_text(list_of_nodes) {
    /* Sorts a list of nodes by text in-place. */
    function compare_text(first, second) {
      var a = first.text;
      var b = second.text;
      if (a < b) {
        return -1;
      }
      else if (a > b) {
        return 1;
      }
      else {
        return 0;
      }
    }
    list_of_nodes.sort(compare_text);
  }
});
