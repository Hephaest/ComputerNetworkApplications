HTTP/1.1 200 OK
Date: Sat, 24 Nov 2018 07:58:03 GMT
Server: Apache
Last-Modified: Wed, 25 Apr 2018 13:30:57 GMT
ETag: "2eb57b6a-5866-56aac47ea2640"
Accept-Ranges: bytes
Content-Length: 22630
Vary: Accept-Encoding,User-Agent
Content-Type: application/x-javascript

/* mh note - generisize */

var LIVESEARCH = LIVESEARCH || {};

(function($){

    LIVESEARCH.functions = new function()
    {
        strSiteURL      = '';
        strAjaxURL      = '';
        strCoursesURL   = '';
        strIncDepts     = '';
        bFilterResults = false;
        arrResults      = null;
        iLatestSearch   = 0;
        iScrollIndex    = 0;

        this.init = function()
        {
            if(jQuery('#frm-course-search').length > 0)
            {
                // intialise variables
                this.arrResults = new Array();

                // get ajax url & course url
                var arrAjaxURL = document.location.toString().match(/https?\:\/\/[^\/]*/);
                if(arrAjaxURL.length > 0)
                {
                    this.strSiteURL = arrAjaxURL[0];
                    this.strAjaxURL = this.strSiteURL+"/media/wdp/style-assets/php/wdp-inc-ajax-search.php";
                    this.setCoursesURL();
                }

                // add result div
                jQuery('#frm-course-search').append(
                    jQuery(document.createElement('div'))
                        .attr("id", "live-search-holder")
                        .addClass("hide hidden")
                );

                // and code to handle keystrokes
                this.iScrollIndex = 0;
                jQuery('#frm-course-search').keyup(this.doSearch);

                // remove keypress event to avoid confusion in some browsers
                jQuery('#frm-course-search').unbind('keypress');

                // also, we'll need to check what to do when they hit enter (it might be submitting
                // the form or it might be loading a particular course they've scrolled to)
                jQuery('#frm-course-search').submit(this.checkSearchSubmission);

                // handle radio button changes on search panel
                this.searchForm();

                // get list of included departments
                if(jQuery('#search-departments').length > 0)
                {
                    this.strIncDepts = jQuery('#search-departments').val();
                }
                if(jQuery('#search-departments-only').length > 0)
                {
                    this.bFilterResults = jQuery('#search-departments-only').val();
                }

                // clear the search results if the user clicks away
                // but *not* if they're clicking on a course search result
                jQuery('#search-query').blur(function() {
                    $(":not(#live-search-holder a)").click(function (e) {
                        // hide the ajax popup, but don't clear the input
                        jQuery('#live-search-holder').addClass("hide hidden");
                    });
                });

                // finally set up the clear search button
                jQuery("#btn-clear-live").click(function() {
                    jQuery('#search-query').val("");
                    LIVESEARCH.functions.doSearch();
                    jQuery("#btn-clear-live").addClass("visuallyhidden");
                });
            }
        }

        this.setCoursesURL = function()
        {
            // retrieve url from form but drop the last but one piece (i.e. the course-search bit)
            // we need to check that the frm-course-search has an action
            if (jQuery('#frm-course-search').attr('action')) {
                var arrURLPieces = jQuery('#frm-course-search').attr('action').split("/");
                arrURLPieces.splice((arrURLPieces.length - 2), 1);
                this.strCoursesURL = arrURLPieces.join("/");
            }
        }

        this.searchForm = function()
        {
            jQuery('#frm-course-search input[type="radio"]').change( function()
            {
                // switch where the form is posted to depending on radio button value
                jQuery('#frm-course-search').attr('action', jQuery(this).attr('data-url'));
                jQuery('#search-query').attr('name', jQuery(this).attr('data-name'));

                // also switch the links under the search box depending on radio choice
                var strCurrentLink = jQuery('#browse-az').attr('href');
                jQuery('#browse-az').attr('href',jQuery('#browse-az').attr('data-switch-url'));
                jQuery('#browse-az').attr('data-switch-url', strCurrentLink);

                strCurrentLink = jQuery('#browse-dept').attr('href');
                jQuery('#browse-dept').attr('href', jQuery('#browse-dept').attr('data-switch-url'));
                jQuery('#browse-dept').attr('data-switch-url', strCurrentLink);

                if ( jQuery('#ug-pg-context').length ) {
                    var strUGPGMessage = jQuery('#ug-pg-context').html().toString();
                    if(strUGPGMessage.indexOf("Undergraduate") > -1)
                        jQuery('#ug-pg-context').html(strUGPGMessage.replace("Under", "Post"))
                    else
                        jQuery('#ug-pg-context').html(strUGPGMessage.replace("Post", "Under"))
                }

                // make sure the search knows we've changed too
                LIVESEARCH.functions.setCoursesURL();
                jQuery('#search-category').val(jQuery(this).val() == "ug" ? "Undergraduate" : "Postgraduate");
             });
        }

        this.doSearch = function(event)
        {
            // check if we're using arrows keys or tab...
            if(event && event.keyCode == '38')
            {
                // up arrow
                LIVESEARCH.functions.scrollResults(false);
            }
            else if(event && event.keyCode == '40')
            {
                // down arrow
                LIVESEARCH.functions.scrollResults(true);
            }
            else if(jQuery('#live-search-holder li.focussed').length> 0 && event && (event.keyCode == '32' || event.keyCode == '39'))
            {
                // space or right arrow
                LIVESEARCH.functions.fireResultLink();
            }
            else if(event && event.keyCode == '9')
            {
                // ignore tab key. allow users to tab through the course list.
                return;
            }
            else
            {
                // clear out any server side results
                jQuery('#server-search-holder').html("");

                // if the query isn't blank
                if(jQuery('#search-query').val() != "")
                {
                    var deptOrFaculty = jQuery('#search-type').attr('name');

                    var deptId = '';
                    var facultyId = '';

                    if ('' !== LIVESEARCH.functions.strIncDepts && undefined !== LIVESEARCH.functions.strIncDepts) {
                        deptId = LIVESEARCH.functions.strIncDepts;
                    } else {
                        if ('f' === deptOrFaculty) {
                            facultyId = jQuery('#search-type').val();
                        } else {
                            deptId = jQuery('#search-type').val();
                        }
                    }

                    // record time
                    LIVESEARCH.functions.iLatestSearch = (new Date()).getTime();

                    jQuery.ajax({
                        url:  LIVESEARCH.functions.strAjaxURL,
                        type: "GET",
                        data: {
                            q : jQuery('#search-query').val(),
                            c : jQuery('#search-category').val(),
                            df : jQuery('#search-data-path').val(),
                            dd : jQuery('#search-data-depth').val(),
                            d : deptId,
                            f : facultyId,
                            l : LIVESEARCH.functions.bFilterResults,
                            t : LIVESEARCH.functions.iLatestSearch
                        },
                        success: function(objData) {
                            LIVESEARCH.functions.onSuccess(objData);
                        },
                        failure: function() {
                            LIVESEARCH.functions.onFailure();
                        }
                    });
                }
                else
                {
                    jQuery('#live-search-holder').addClass("hide hidden");
                }
            }

            return false;
        }

        this.scrollResults = function(bDown)
        {
            // adjust accordingly
            if(bDown == true)
                    this.iScrollIndex++;
            else
                    this.iScrollIndex--;

            // check boundries
            if(this.iScrollIndex < 0)
                    this.iScrollIndex = 0;
            else if(this.iScrollIndex > jQuery('#live-search-holder li').length)
                    this.iScrollIndex = jQuery('#live-search-holder li').length;

            // apply focus class
            jQuery('#live-search-holder li').each(
                function(iIndex, objItem) {
                    if ((iIndex+1) == LIVESEARCH.functions.iScrollIndex)
                        jQuery(objItem).addClass('focussed');
                    else
                        jQuery(objItem).removeClass('focussed');
                }
            );
        }

        this.fireResultLink = function()
        {
            // redirect the browser to the current active item in the result list
            window.location.href = jQuery('#live-search-holder li.focussed a').attr('href');
        }

        this.checkSearchSubmission = function()
        {
            // if the user pressed enter check whether they'd scrolled to something first
            if(LIVESEARCH.functions.iScrollIndex > 0)
            {
                // if they have, load the relevant course page ... otherwise just continue & submit the form as normal
                LIVESEARCH.functions.fireResultLink();
                return false;
            }
        }

        this.onSuccess = function(objResponseXML)
        {
            if(objResponseXML)
            {
                for(var iLoop = 0; iLoop < objResponseXML.childNodes.length; iLoop++)
                {
                    var objResponseRoot = objResponseXML.childNodes[iLoop];
                    if(objResponseRoot.nodeName == "response")
                    {
                        this.arrResults = new Array();

                        var ndsNewsInfo    = objResponseRoot.childNodes;
                        for(var jLoop = 0; jLoop < ndsNewsInfo.length; jLoop++)
                        {
                            if(ndsNewsInfo[jLoop].nodeName == "result")
                            {
                                var slug = '';

                                if (undefined !== ndsNewsInfo[jLoop].attributes['slug']) {
                                    slug = ndsNewsInfo[jLoop].attributes['slug'].nodeValue.toString();
                                }

                                var note = '';

                                if (undefined !== ndsNewsInfo[jLoop].attributes['note']) {
                                    note = ndsNewsInfo[jLoop].attributes['note'].nodeValue.toString();
                                }

                                var param = '';

                                if (undefined !== ndsNewsInfo[jLoop].attributes['param']) {
                                    param = ndsNewsInfo[jLoop].attributes['param'].nodeValue.toString();
                                }

                                var category = '';

                                if (undefined !== ndsNewsInfo[jLoop].attributes['category']) {
                                    category = ndsNewsInfo[jLoop].attributes['category'].nodeValue.toString();
                                }

                                this.arrResults.push({
                                    title: ndsNewsInfo[jLoop].firstChild.nodeValue.toString(),
                                    slug: slug,
                                    category: category,
                                    note: note,
                                    param: param
                                });
                            }
                        }

                        // if this lot of xml we've got back corresponds to the latest search done by the user then output it
                        if(this.iLatestSearch == parseInt(objResponseRoot.attributes.getNamedItem("requested").value, 10)) {
                            this.processResults();
                        }
                    }
                }
            }
        }

        this.processResults = function()
        {
            var iMaxToDisplay = 10;

            // delete contents of result holder and make sure its showing
            jQuery('#live-search-holder').html("")
                                         .removeClass("hide hidden");

            var combinedResults = jQuery('#search-category').val() === 'All' ? true : false;

            if(combinedResults) {
                var iResults = this.arrResults.length;
                var iMaxToDisplay = 3;
                var ugCourses = new Array();
                var pgCourses = new Array();

                // loop and put course results into UG or PG array
                for (var kLoop = 0; kLoop < iResults; kLoop++) {
                    if (this.arrResults[kLoop].category === 'Postgraduate') {
                        pgCourses.push(this.arrResults[kLoop]);
                    } else {
                        ugCourses.push(this.arrResults[kLoop]);
                    }
                }
                
                var ugResults = ugCourses.length;
                // show ug courses
                if (ugResults > 0) {
                    jQuery('#live-search-holder').append(jQuery(document.createElement('h3')).html('Undergraduate Courses'));
                    jQuery('#live-search-holder').append(jQuery(document.createElement('ul')).addClass("resultlist ug"));
                    var url = jQuery('#frm-course-search').attr('data-ugurl');
                    var iMaxToShow = (bMainSearchPage ? ugResults : Math.min(ugResults, iMaxToDisplay));
                    for (var xLoop = 0; xLoop < iMaxToShow; xLoop++) {
                        var slug = '';

                        if (ugCourses[xLoop].slug === '') {
                            slug = this.createUrl(ugCourses[xLoop].title);
                        } else {
                            slug = ugCourses[xLoop].slug;
                        }

                        jQuery('.resultlist.ug').append
                        (
                            jQuery(document.createElement('li')).append
                            (
                                jQuery(document.createElement('a'))
                                    .html(ugCourses[xLoop].title + ugCourses[xLoop].note)
                                    .attr('href', url + slug + '/' + ugCourses[xLoop].param)
                            )
                        );
                    }

                    if (ugCourses.length > iMaxToDisplay) {
                        jQuery('.resultlist.ug').append
                        (
                            jQuery(document.createElement('li')).append
                            (
                                jQuery(document.createElement('a'))
                                    .attr('href', url + '?q=' + escape(jQuery('#search-query').val()))
                                    .html('More courses found')
                            )
                            .addClass('ajax-view-results')
                        );
                    }
                }
                
                var pgResults = pgCourses.length;
                // show pg courses
                if (pgResults > 0) {
                    jQuery('#live-search-holder').append(jQuery(document.createElement('h3')).html('Postgraduate Courses'));
                    jQuery('#live-search-holder').append(jQuery(document.createElement('ul')).addClass("resultlist pg"));
                    var url = jQuery('#frm-course-search').attr('data-pgurl');
                    var iMaxToShow = (bMainSearchPage ? pgResults : Math.min(pgResults, iMaxToDisplay));
                    for (var yLoop = 0; yLoop < iMaxToShow; yLoop++) {
                        var slug = '';

                        if (pgCourses[yLoop].slug === '') {
                            slug = this.createUrl(pgCourses[yLoop].title);
                        } else {
                            slug = pgCourses[yLoop].slug;
                        }

                        jQuery('.resultlist.pg').append
                        (
                            jQuery(document.createElement('li')).append
                            (
                                jQuery(document.createElement('a'))
                                    .html(pgCourses[yLoop].title)
                                    .attr('href', url + slug + '/')
                            )
                        )
                    }

                    if (pgCourses.length > iMaxToDisplay) {
                        jQuery('.resultlist.pg').append
                        (
                            jQuery(document.createElement('li')).append
                            (
                                jQuery(document.createElement('a'))
                                    .attr('href', url + '?q=' + escape(jQuery('#search-query').val()))
                                    .html('More courses found')
                            )
                            .addClass('ajax-view-results')
                        );
                    }
                }

                if (ugResults === 0 && pgResults === 0 && jQuery('#search-query').val() != "") {
                    jQuery('#live-search-holder').append(
                        jQuery(document.createElement('p'))
                            .html("No results were found")
                            .addClass('ajax-no-results')
                    );
                }

            } else {
                if(this.arrResults.length > 0)
                {
                    var bMainSearchPage = jQuery('body').hasClass('course-search');

                    // create and append a new list
                    jQuery('#live-search-holder').append(
                        jQuery(document.createElement('ul'))
                            .addClass("resultlist")
                    );

                    // add data into the apge
                    var iResults = this.arrResults.length;
                    var iMaxToShow = (bMainSearchPage ? iResults : Math.min(iResults, iMaxToDisplay));
                    for(var kLoop = 0; kLoop < iMaxToShow; kLoop++)
                    {
                        var slug = '';

                        if (this.arrResults[kLoop].slug === '') {
                            slug = this.createURL(this.arrResults[kLoop].title);
                        } else {
                            slug = this.arrResults[kLoop].slug;
                        }

                        jQuery('.resultlist').append
                        (
                            jQuery(document.createElement('li')).append
                            (
                                jQuery(document.createElement('a'))
                                    .html(this.arrResults[kLoop].title + this.arrResults[kLoop].note)
                                    .attr('href', this.strCoursesURL + slug + '/' + this.arrResults[kLoop].param)
                            )
                        );
                    }

                    this.appendLink('.resultlist', iMaxToDisplay, iResults, jQuery('#frm-course-search').attr('action'));

                }
                else if(jQuery('#search-query').val() != "")
                {
                    // let the user know that nothing was found
                    jQuery('#live-search-holder').append(
                        jQuery(document.createElement('p'))
                            .html("No results were found")
                            .addClass('ajax-no-results')
                    );

                    // make sure our clear button is visible
                    jQuery("#btn-clear-live").removeClass("visuallyhidden");
                }
            }
        }

        this.appendLink = function(resultClass, maxDisplay, resultCount, url)
        {
            // make sure our clear button is visible
            jQuery("#btn-clear-live").removeClass("visuallyhidden");

            var bMainSearchPage = jQuery('body').hasClass('course-search');

            var strLinkText = "";

            if(resultCount == 1)
            {    strLinkText = "View this result";   }
            else if(resultCount < maxDisplay)
            {    strLinkText = "View these results";   }
            else
            {    strLinkText = "View all " +resultCount+ " results";   }

            // add a link to all results (if we're not on the results page already)
            if(!bMainSearchPage)
            {
                jQuery(resultClass).append
                (
                    jQuery(document.createElement('li')).append
                    (
                        jQuery(document.createElement('a'))
                            .attr('href', url+'?q='+escape(jQuery('#search-query').val()))
                            .html(strLinkText)
                    )
                    .addClass('ajax-view-results')
                );
            }
        }

        this.createURL = function(strTitle)
        {
            // strip all non alpha numerics and replace spaces with hyphens and then tolower the result
            return strTitle.replace(/[^a-z0-9 ]*/gi, '').replace(/ +/gi, '-').toLowerCase();
        }

        this.onFailure = function()
        {
            alert("An error occurred");
        }
    }
    LIVESEARCH.functions.init();

})(jQuery);
