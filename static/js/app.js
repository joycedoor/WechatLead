function collectActionData() {
    return {
        'Status': $('#Status').val(),
        'Student_or_Parent__c': $('#Student_or_Parent__c').val(),
        'LastName': $('#LastName').val(),
        'Account__c': $('#Account__c').val(),
        'Social_Media_Platform__c': $('#Social_Media_Platform__c').val(),
        'WeChat_Agents_List__c': $('#WeChat_Agents_List__c').val(),
        'WeCom_Agents_List__c': $('#WeCom_Agents_List__c').val(),
        'Sales_WeChat_Account__c': $('#Sales_WeChat_Account__c').val(),
        'Group_Name__c': $('#Group_Name__c').val(),
        'Member_First_Name__c': $('#Member_First_Name__c').val(),
        'Member_Last_Name__c': $('#Member_Last_Name__c').val(),
        'Date_of_Birth__c': $('#Date_of_Birth__c').val(),
        'Email': $('#Email').val()
    };
}

$(document).ready(function() {

    $('#Status, #LastName, #Social_Media_Platform__c, #WeChat_Agents_List__c, #WeCom_Agents_List__c').change(function() {
        // 获取必填字段的值
        var leadStatus = $('#Status').val();
        var lastName = $('#LastName').val();
        var socialMediaPlatform = $('#Social_Media_Platform__c').val();
        var weChatAgent = $('#WeChat_Agents_List__c').val();
        var weComAgent = $('#WeCom_Agents_List__c').val();

        // 检查必填字段是否已填写
        var isFilled = leadStatus && lastName && socialMediaPlatform;
        // 检查至少选择了一个Agent list
        var isAgentSelected = weChatAgent || weComAgent;

        // 如果所有条件都满足，则启用提交按钮
        if (isFilled && isAgentSelected) {
            $('#submit-action').removeAttr('disabled');
        } else {
            $('#submit-action').attr('disabled', 'disabled');
        }
    });

    $('.select2').select2({
        placeholder: 'Select a school',
        allowClear: true
    });

    // 从后端获取数据填充下拉框
    $.ajax({
        url: '/get_school_names',  
        type: 'GET',
        dataType: 'json',
        success: function(data) {
            var select = $('#Account__c');
            select.empty(); // 清空现有的选项
            data.forEach(function(name) {
                select.append(new Option(name, name));  // 这里假设每个学校的名称都是唯一的
            });
        }
    });

    $('#refresh_data').click(function() {
        // 显示模态框
        $('#loadingModal').modal('show');
    
        $.get('/refresh_data', function(data) {
            // 解析返回的 JSON 数据并更新页面
            $('#contact-list').empty(); // 清空当前列表
            $.each(data.contacts_info, function(index, contact) {
                $('#contact-list').append(
                    `<li class="list-group-item contact-item" data-user-id="${index}">
                        ${contact[0]} (${contact[2]})
                        ${data.initial_values[index] && data.initial_values[index]['is_in_SF'] == 1 ? '<span class="badge badge-success" style="margin-left: 10px;">已存在Leads</span>' : ''}
                    </li>`
                );
            });
    
            // 隐藏模态框
            $('#loadingModal').modal('hide');
            alert('Refresh data fetched!');
        }).fail(function() {
            // 如果请求失败，也关闭模态框，并通知用户
            $('#loadingModal').modal('hide');
            alert('Error fetching data');
        });
    });

    $('#Social_Media_Platform__c').change(function() {
        var platform = $(this).val();
        // 根据选择显示/隐藏 WeChat 或 WeCom 代理列表
        if(platform === "WeChat") {
            $('#WeChat_Agents_List__c_container').show();
            $('#WeCom_Agents_List__c_container').hide();
        } else if(platform === "WeCom") {
            $('#WeCom_Agents_List__c_container').show();
            $('#WeChat_Agents_List__c_container').hide();
        } else {
            $('#WeChat_Agents_List__c_container').hide();
            $('#WeCom_Agents_List__c_container').hide();
        }
    });

    $(document).on('click', '.contact-item', function() {
        var userId = $(this).data('user-id');
        var self = this; // 保存 this 的引用

        $.getJSON('/get_initial_values', function(data) {
            var userValues = data[userId];
            $('.contact-item').removeClass('active');
            $(self).addClass('active');
            $('.chat-messages').empty(); // 使用 . 而不是 # 来选中 class

            var formElementIds = [
                "Status",
                "Student_or_Parent__c",
                "LastName",
                "Account__c",
                "Social_Media_Platform__c",
                "WeChat_Agents_List__c",
                "WeCom_Agents_List__c",
                "Sales_WeChat_Account__c",
                "Group_Name__c",
                "Member_First_Name__c",
                "Member_Last_Name__c",
                "Date_of_Birth__c",
                "Email"
            ];

            formElementIds.forEach(function(id) {
                // 如果 initial_values 中有对应的值，则使用它，否则设置为空字符串
                var value = userValues && userValues[id] ? userValues[id] : '';
                if(id === "Account__c") {
                    // 对于Select2控件，使用特定的方法来更新值
                    $('#Account__c').val(value).trigger('change');
                    if(!value) {
                        // 如果没有值，则重置Select2以显示占位符
                        $('#Account__c').val(null).trigger('change');
                    }
                } else {
                    $('#' + id).val(value);
                }

                // 特殊处理下拉框显示/隐藏逻辑
                if(id === "Social_Media_Platform__c" && value) {
                    if(value === "WeChat") {
                        $('#WeChat_Agents_List__c_container').show();
                        $('#WeCom_Agents_List__c_container').hide();
                    } else if(value === "WeCom") {
                        $('#WeCom_Agents_List__c_container').show();
                        $('#WeChat_Agents_List__c_container').hide();
                    }
                }
            });

            // 如果没有对应的用户数据，隐藏所有条件性显示的字段
            if(!userValues) {
                $('#WeChat_Agents_List__c_container').hide();
                $('#WeCom_Agents_List__c_container').hide();
            }

            // 发送 AJAX 请求获取聊天记录
            $.getJSON('/get_messages/' + userId, function(user_messages) {
                if(user_messages.length > 0) {
                    user_messages.forEach(function(msg) {
                        var [message, issender, timestamp] = msg;
                        var messageElement = $('<div></div>');
                        var date = new Date(timestamp * 1000);
                        var formattedTime = date.toLocaleString();
                        messageElement.html(`<strong>${issender ? 'You' : 'Contact'}:</strong> ${message} <small>${formattedTime}</small>`);
                        messageElement.addClass(issender ? 'sent-message' : 'received-message');
                        $('.chat-messages').append(messageElement); // 使用 . 而不是 #
                    });
                } else {
                    $('.chat-messages').append($('<div></div>').text('No messages found.'));
                }
            }).fail(function() {
                console.log("Error fetching messages");
            });
        });

        
    });

    $('#submit-action').click(function() {
        var userId = $('.contact-item.active').data('user-id');
        var actionData = collectActionData(); 
        $.ajax({
            url: '/submit_action',
            type: 'POST',
            contentType: 'application/json', // 指定发送的数据类型为 JSON
            data: JSON.stringify({ user_id: userId, action_data: actionData }), // 将数据转换为 JSON 字符串
            success: function(response) {
                console.log(response);
                if(response.status === 'success') {
                    // 添加已存在Leads的标签
                    //$('.contact-item.active').append('<span class="badge badge-success" style="margin-left: 10px;">已存在Leads</span>');
                    
                    alert('Leads创建成功！')

                    // 页面提交成功后刷新
                    location.reload();
                } else if (response.status === 'Failed') {
                    alert('操作失败，请重试！');
                }
            },
            error: function() {
                console.log("Error submitting action");
            }
        });
    });
});