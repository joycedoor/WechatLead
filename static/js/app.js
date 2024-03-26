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
        'Email': $('#Email').val(),
        'Note_and_Description__c': $('#Note_and_Description__c').val()
    };
}

function extractContent(s) {
    var match = s.match(/\(([^)]+)\)(?!.*\()/); // 仅匹配最后一对括号内的内容
    return match ? match[1] : '';
}

function findSchoolAbbreviation(target, schools) {
    var foundSchool = ''; // 默认为空值
    target = target.toLowerCase(); // 将目标文本转换为小写以进行比较

    // 遍历学校列表
    schools.forEach(school => {
        var abbreviation = school.abbreviation.toLowerCase(); // 将缩写转换为小写
        var regex = new RegExp('\\b' + RegExp.escape(abbreviation) + '\\b'); // 创建正则表达式

        // 如果找到匹配的缩写，则设置学校的全称
        if (regex.test(target)) {
            foundSchool = school.schoolName;
        }
    });

    return foundSchool;
}

// 为 RegExp 添加 escape 方法
if (!RegExp.escape) {
    RegExp.escape = function(s) {
        return String(s).replace(/[\\^$*+?.()|[\]{}]/g, '\\$&');
    };
}

function filterContactsWithoutLeads() {
    const isChecked = $('#hide-lead-checkbox').is(':checked');
    $('.contact-item').each(function() {
        const hasLead = $(this).find('.badge-success').length > 0;
        const iswl = $(this).find('.badge-white').length > 0;
        if (isChecked && (hasLead || iswl)) {
            $(this).hide();
        } else {
            $(this).show();
        }
    });
}

// 辅助函数，用于标记未填写的字段
function markUnfilled(selector, isFilled) {
    if (!isFilled) {
        $(selector).css('border-color', 'red'); // 未填写的字段边框变红
    } else {
        $(selector).css('border-color', ''); // 恢复正常边框颜色
    }
}

$(document).ready(function() {

    // 新增筛选联系人的逻辑
    $('#hide-lead-checkbox').change(function() {
        filterContactsWithoutLeads();
    });
    filterContactsWithoutLeads();

    $('#schoolModal').on('shown.bs.modal', function () {
        // 先清空现有的行
        $('#addedRows').empty();
        // 从 localStorage 中读取数据
        var storedData = localStorage.getItem('schoolData');
        if (storedData) {
            var schoolData = JSON.parse(storedData);
            schoolData.forEach(function(data) {
                // 这里应该是您添加新行到界面的代码
                $('#addedRows').append(
                    '<div class="row school-row">' +
                    '<span class="school-name">' + data.schoolName + '</span> - ' +
                    '<span class="school-abbreviation">' + data.abbreviation + '</span>' +
                    '</div>'
                );
            });
        }
        $('#schoolSelect').select2({
            placeholder: 'Select a school',
            allowClear: true,
            dropdownParent: $('#schoolModal') // 确保下拉列表渲染在模态框内
        });
    });

    $('.select2').not('#schoolSelect').select2({
        placeholder: 'Select a school',
        allowClear: true
    });

    // 添加学校缩写点击显示模态框
    $('#school_nickname').click(function() {
        $('#schoolModal').modal('show');
    });

    // 添加白名单点击显示模态框
    $('#add_to_whitelist').click(function() {
        if ($('.contact-item.active').length > 0) {
            $('#whitelistModal').modal('show');
        } else {
            alert('请先选择一个联系人！');
        }
    });
    // 添加白名单按钮的确认事件
    $('#confirmAddToWhitelist').click(function() {
        var userId = $('.contact-item.active').data('user-id');
        if (userId) {
            var whitelist = localStorage.getItem('whitelist') ? JSON.parse(localStorage.getItem('whitelist')) : [];
            if (!whitelist.includes(userId)) {
                whitelist.push(userId);
                localStorage.setItem('whitelist', JSON.stringify(whitelist));
                $('.contact-item.active').append('<span class="badge badge-white" style="margin-left: 10px;">白名单</span>');
                alert('已成功添加到白名单！');
            } else {
                alert('此联系人已在白名单中。');
            }
        }
        $('#whitelistModal').modal('hide');
    });

    function updateContactListTags() {
        var whitelist = localStorage.getItem('whitelist') ? JSON.parse(localStorage.getItem('whitelist')) : [];
        $('.contact-item').each(function() {
            var userId = $(this).data('user-id');
            if (whitelist.includes(userId) && !$(this).find('.badge-white').length) {
                $(this).append('<span class="badge badge-white" style="margin-left: 10px;">白名单</span>');
            }
        });
    }
    updateContactListTags(); // 初次加载时更新

    // 添加行的逻辑
    $('#addRow').click(function() {
        var schoolName = $('#schoolSelect').val();
        var abbreviation = $('#schoolAbbreviation').val();
        // 检查是否已填写学校名和缩写
        if (schoolName && abbreviation) {
            // 添加新行到界面，同时添加类名以便于识别
            $('#addedRows').append(
                '<div class="row school-row">' + // 添加类名 'school-row' 用于识别这些行
                '<span class="school-name">' + schoolName + '</span> - ' + // 添加类名 'school-name'
                '<span class="school-abbreviation">' + abbreviation + '</span>' + // 添加类名 'school-abbreviation'
                '</div>'
            );
            // 清空表单以供下次输入
            $('#schoolAbbreviation').val('');
        } else {
            // 如果学校名或缩写未填写，则提醒用户
            alert('Please fill in both the school name and abbreviation.');
        }
    });

    // 保存更改的逻辑
    $('#saveChanges').click(function() {
        var schoolData = [];
        $('.school-row').each(function() { // 改为遍历所有 '.school-row'
            var row = $(this);
            console.log(row);
            var schoolName = row.find('.school-name').text();
            var abbreviation = row.find('.school-abbreviation').text();
            schoolData.push({schoolName: schoolName, abbreviation: abbreviation});
        });
        if (schoolData) {
            console.log(schoolData);
            localStorage.setItem('schoolData', JSON.stringify(schoolData)); // 将数据保存到 localStorage
        } else {
            alert('没有数据需要保存！');
        }
        $('#schoolModal').modal('hide');
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
            var select = $('#schoolSelect');
            select.empty(); // 清空现有的选项
            data.forEach(function(name) {
                select.append(new Option(name, name));
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
                        ${contact['Alias']} (${contact['Remark']})
                        ${data.initial_values[index] && data.initial_values[index]['is_in_SF'] == 1 ? '<span class="badge badge-success" style="margin-left: 10px;">已存在Leads</span>' : ''}
                    </li>`
                );
            });
    
            // 隐藏模态框
            updateContactListTags(); 
            $('#loadingModal').modal('hide');
            alert('数据刷新成功！');
        }).fail(function() {
            // 如果请求失败，也关闭模态框，并通知用户
            $('#loadingModal').modal('hide');
            alert('获取数据失败，请联系管理员');
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
        updateContactListTags(); // 每次点击更新
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
            if(!userValues["Social_Media_Platform__c"]) {
                $('#WeChat_Agents_List__c_container').hide();
                $('#WeCom_Agents_List__c_container').hide();
            }

            //处理学校
            if (!userValues["Account__c"]){
                var selfContent = extractContent(self.innerHTML); // 提取括号内的内容
                // 从 localStorage 中获取学校数据
                console.log(selfContent);
                var storedSchoolData = localStorage.getItem('schoolData');
                var schools = storedSchoolData ? JSON.parse(storedSchoolData) : [];
                console.log(schools);
                var schoolFullName = findSchoolAbbreviation(selfContent, schools);
                console.log(schoolFullName);
                $('#Account__c').val(schoolFullName).trigger('change');
                if(!schoolFullName) {
                    // 如果没有值，则重置Select2以显示占位符
                    $('#Account__c').val(null).trigger('change');
                }
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

    $('#submit-action').click(function(e) {
        e.preventDefault(); // 阻止表单的默认提交行为
    
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
    
        // 检查所有条件是否满足
        if (isFilled && isAgentSelected) {
            // 所有条件都满足，发送数据
            var userId = $('.contact-item.active').data('user-id');
            var actionData = collectActionData();
            $.ajax({
                url: '/submit_action',
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ user_id: userId, action_data: actionData }),
                success: function(response) {
                    console.log(response);
                    if(response.status === 'success') {
                        alert('Leads创建成功！');
                        location.reload();
                        updateContactListTags(); 
                    } else if (response.status === 'Failed') {
                        alert('操作失败，请截图页面以及console内容，联系管理员处理！');
                    }
                },
                error: function() {
                    console.log("Error submitting action");
                }
            });
        } else {
            // 条件不满足，标记必填字段
            markUnfilled('#Status', leadStatus);
            markUnfilled('#LastName', lastName);
            markUnfilled('#Social_Media_Platform__c', socialMediaPlatform);
            if (!weChatAgent && !weComAgent) { // 如果两个都未选择
                markUnfilled('#WeChat_Agents_List__c', false);
                markUnfilled('#WeCom_Agents_List__c', false);
            }
        }
    });
});